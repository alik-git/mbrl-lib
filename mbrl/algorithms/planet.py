import pathlib
from typing import List

import numpy as np
import omegaconf
import torch
from gym.wrappers import TimeLimit

import mbrl.constants
from mbrl.env.termination_fns import no_termination
from mbrl.models import ModelEnv, ModelTrainer, PlaNetModel
from mbrl.planning import (
    RandomAgent,
    complete_agent_cfg,
    create_trajectory_optim_agent_for_model,
)
from mbrl.third_party.dmc2gym.wrappers import DMCWrapper
from mbrl.util import Logger, ReplayBuffer
from mbrl.util.common import get_sequence_buffer_iterator, rollout_agent_trajectories
from mbrl.util.mujoco import rollout_mujoco_env

META_LOG_FORMAT = [
    ("reconstruction_loss", "OL", "float"),
    ("reward_loss", "RL", "float"),
    ("gradient_norm", "GN", "float"),
    ("kl_loss", "KL", "float"),
]

device = "cuda:0"


env = TimeLimit(
    DMCWrapper(
        "cheetah",
        "run",
        task_kwargs={"random": 0},
        visualize_reward=False,
        height=64,
        width=64,
        from_pixels=True,
        frame_skip=4,
    ),
    max_episode_steps=1000,
)


# This is the stuff to be replaced with a config file
action_repeat = 4
num_steps = 1000000 // action_repeat
num_grad_updates = 1000
sequence_length = 50
trajectory_length = 1000
batch_size = 50
num_initial_trajectories = 5
agent_noise = 0.3
free_nats = 3
kl_scale = 1.0
test_frequency = 25
use_agent_callback = False
agent_cfg = omegaconf.OmegaConf.create(
    {
        "_target_": "mbrl.planning.TrajectoryOptimizerAgent",
        "action_lb": "???",
        "action_ub": "???",
        "planning_horizon": 12,
        "optimizer_cfg": {
            "_target_": "mbrl.planning.CEMOptimizer",
            "num_iterations": 10,
            "elite_ratio": 0.1,
            "population_size": 1000,
            "alpha": 0.1,
            "lower_bound": "???",
            "upper_bound": "???",
            "return_mean_elites": True,
            "device": device,
        },
        "replan_freq": 1,
        "verbose": True,
    }
)
agent_cfg = complete_agent_cfg(env, agent_cfg)


replay_buffer = ReplayBuffer(
    num_steps,
    env.observation_space.shape,
    env.action_space.shape,
    obs_type=np.uint8,
    max_trajectory_length=trajectory_length,
)
total_rewards = rollout_agent_trajectories(
    env,
    num_initial_trajectories,
    RandomAgent(env),
    agent_kwargs={},
    replay_buffer=replay_buffer,
    collect_full_trajectories=True,
    trial_length=trajectory_length,
    agent_uses_low_dim_obs=False,
)

planet = PlaNetModel(
    (3, 64, 64),
    1024,
    ((3, 32, 4, 2), (32, 64, 4, 2), (64, 128, 4, 2), (128, 256, 4, 2)),
    ((1024, 1, 1), ((1024, 128, 5, 2), (128, 64, 5, 2), (64, 32, 6, 2), (32, 3, 6, 2))),
    30,
    env.action_space.shape[0],
    200,
    200,
    device,
    free_nats_for_kl=free_nats,
    kl_scale=kl_scale,
)
rng = torch.Generator(device=device)
rng.manual_seed(0)
np_rng = np.random.default_rng(seed=0)
model_env = ModelEnv(env, planet, no_termination, generator=rng)

agent = create_trajectory_optim_agent_for_model(model_env, agent_cfg)

rec_losses: List[float] = []
reward_losses: List[float] = []
kl_losses: List[float] = []
grad_norms: List[float] = []


def clear_log_containers():
    rec_losses.clear()
    reward_losses.clear()
    kl_losses.clear()
    grad_norms.clear()


def batch_callback(_epoch, _loss, meta, _mode):
    if meta:
        rec_losses.append(np.sqrt(meta["reconstruction_loss"] / (3 * 64 * 64)))
        reward_losses.append(meta["reward_loss"])
        kl_losses.append(meta["kl_loss"])
        grad_norms.append(meta["grad_norm"])


exp_name = f"fourth_try___ngu{num_grad_updates}"
save_dir = (
    pathlib.Path("/checkpoint/lep/mbrl/planet/dm_cheetah_run/full_model") / exp_name
)

save_dir.mkdir(exist_ok=True, parents=True)

logger = Logger(save_dir)
trainer = ModelTrainer(planet, logger=logger, optim_lr=1e-3, optim_eps=1e-4)
logger.register_group("meta", META_LOG_FORMAT, color="yellow")
logger.register_group(
    mbrl.constants.RESULTS_LOG_NAME, mbrl.constants.EVAL_LOG_FORMAT, color="green"
)

next_obs = None
episode_reward = None
random_agent = RandomAgent(env)
done = True
# start of loop will train, then increase this to 0
current_episode = -1


def is_test_episode(episode_):
    return episode_ >= 0 and (episode_ % test_frequency == 0)


def agent_callback(population, values, i):
    if not use_agent_callback:
        return

    init_obs = obs
    how_many = 100
    lookahead = population.shape[-2]
    seen_values = torch.empty(how_many, 1)
    for k in range(how_many):
        plan = population[k].cpu().numpy()
        pred_obs, pred_rewards, _ = rollout_mujoco_env(
            env, init_obs, lookahead, plan=plan
        )
        assert pred_rewards.size == lookahead
        seen_values[k] = pred_rewards.sum()

    corr = np.corrcoef(seen_values.squeeze(), values[:how_many].cpu().numpy())[0, 1]
    if i == 0:
        print(corr)
    return


for step in range(num_steps):
    if done:
        # this refers to the episode that just finished
        if is_test_episode(current_episode):
            logger.log_data(
                mbrl.constants.RESULTS_LOG_NAME,
                {
                    "episode_reward": episode_reward or 0.0,
                    "env_step": step,
                },
            )

        obs = env.reset()
        agent.reset()

        # Train the model for one epoch of `num_grad_updates`
        dataset, _ = get_sequence_buffer_iterator(
            replay_buffer,
            batch_size,
            0,
            sequence_length,
            ensemble_size=1,
            max_batches_per_loop_train=num_grad_updates,
        )
        num_epochs = (num_grad_updates - 1) // len(dataset) + 1  # int ceiling
        trainer.train(dataset, num_epochs=num_epochs, batch_callback=batch_callback)

        planet.save(save_dir / "planet.pth")
        replay_buffer.save(save_dir)

        logger.log_data(
            "meta",
            {
                "reconstruction_loss": np.mean(rec_losses),
                "reward_loss": np.mean(reward_losses),
                "gradient_norm": np.mean(grad_norms),
                "kl_loss": np.mean(kl_losses),
            },
        )
        print(f"num_batches: {len(rec_losses)}")
        clear_log_containers()

        episode_reward = 0
        current_episode += 1
    else:
        obs = next_obs

    action_noise = (
        0
        if is_test_episode(current_episode)
        else agent_noise * np_rng.standard_normal(env.action_space.shape[0])
    )
    action = agent.act(obs, optimizer_callback=agent_callback) + agent_noise
    action = np.clip(action, -1.0, 1.0)
    next_obs, reward, done, info = env.step(action)
    replay_buffer.add(obs, action, next_obs, reward, done)
    episode_reward += reward
    print(f"step: {step}, reward: {reward}.")
