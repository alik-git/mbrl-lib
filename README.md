[![PyPi Version](https://img.shields.io/pypi/v/mbrl)](https://pypi.org/project/mbrl/)
[![Main](https://github.com/facebookresearch/mbrl-lib/workflows/CI/badge.svg)](https://github.com/facebookresearch/mbrl-lib/actions?query=workflow%3ACI)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/facebookresearch/mbrl-lib/tree/main/LICENSE)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
# Reinforcement Learning in Duckietown using MBRL
*** Introduction thing citation plagiarism [paper](https://arxiv.org/abs/2104.10159). 
## Missing

Cuda/intro (Ali)

MBRL key attributes overview

License

Citation

## Virtual environement setup
We recommend using [anaconda](https://docs.anaconda.com/anaconda/install/linux/)'s virtual environements and the python version 3.8.

    conda create --name RlDuckie python=3.8
 Then activate it
 
    conda activate RlDuckie
## Gym-Duckietown
<!-- You will need to do the [duckietown laptop](https://docs.duckietown.org/daffy/opmanual_duckiebot/out/laptop_setup.html) setup to use the gym-duckietown -->

Then clone [Gym-Duckietown](https://github.com/duckietown/gym-duckietown.git) and navigate to the master branch

    git clone https://github.com/duckietown/gym-duckietown.git
    cd gym-duckietown 
    git checkout master
    pip3 install -e .
    pip install torch

To import from duckietown gym into mbrl, you will need to add a path (.pth) file to your python installation.
You can find your python installation (whether it is in a virtual environment or not) by using the Python shell. Use these commands:
<!-- A simple way to do so is to run the python command in youre conda virtual environement and print the sys.path files path. -->

    $ python
    Python 3.8.12 (default, Oct 12 2021, 13:49:34) 
    [GCC 7.5.0] :: Anaconda, Inc. on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import sys
    >>> for p in sys.path:
    ...     print(p)
    ... 
    
Which will output something similar to this:

    ~/path/to/mbrl-lib
    ~/path/to/gym-duckietown
    ~/anaconda3/envs/your_python_env_name/lib/python38.zip
    ~/anaconda3/envs/your_python_env_name/lib/python3.8
    ~/anaconda3/envs/your_python_env_name/lib/python3.8/lib-dynload
    ~/.local/lib/python3.8/site-packages
    ~/anaconda3/envs/your_python_env_name/lib/python3.8/site-packages
    >>> 

Then go to ~/anaconda3/envs/your_python_env_name/lib/python3.8/site-packages

There you will find some .pth files, make a new one called duckietowngym.pth (name is not important, you can call it whatever you would like) and make this the content: 

    import sys
    sys.path.append('path/to/gym-duckietown')

Now restart the terminal and python should be able to find gym-duckietown for imports.

## MBRL-Lib
## Getting Started
#### Developer installation
Clone the repository and set up a development environment as follows (Run this command where you'd like your MBRL-Lib installation to be)

    git clone https://github.com/alik-git/mbrl-lib
    cd mbrl-lib
    conda activate RlDuckie
    pip install -e ".[dev]"
    pip install wandb
    conda install pandas

And test it by running the following from the root folder of the repository

    python -m pytest tests/core
    python -m pytest tests/algorithms

## Supported environments
### Dependencies
#### mujoco
Do the "install MuJoCo" and "Install and use mujoco-py" paragraphs from [`mujoco-py`](https://github.com/openai/mujoco-py)

To use mujoco you MAY need to install these packages
   
    sudo apt install curl git libgl1-mesa-dev libgl1-mesa-glx libglew-dev \
    libosmesa6-dev software-properties-common net-tools unzip vim \
    virtualenv wget xpra xserver-xorg-dev libglfw3-dev patchelf
    
You may need to modify some environment variables to get this setup to work, you can do that permanently by editing your [bashrc file](https://rc-docs.northeastern.edu/en/latest/using-discovery/bashrc.html). 


For mujoco you will need to add these path to youre LD_LIBRARY_PATH, we suggest you add it to your .bashrc files in the hidden files on your home, simply paste the line at the end of the file. While you are there you should add the PYTHONPATH to your gym-duckietown, because we found it prevents some imports problem.
You can also run the lines every time you enter a new terminal

    export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:<change this for youre path to .mujoco>/.mujoco/mujoco210/bin"
    export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/usr/lib/nvidia"
    export PYTHONPATH="${PYTHONPATH}:<path to your clone of gym-duckietown>"
    
To test if it works run

    python -m pytest tests/mujoco
    
#### dm_control
Install [`dm_control`](https://github.com/deepmind/dm_control) by running this command

    pip install dm_control

#### openAI Gym
Install [`openAI gym`](https://github.com/openai/gym) by runnig this command

    pip install gym
   
## Visualization
You'll have to create an account and to get all set here is their quickstart [tutorial](https://docs.wandb.ai/quickstart).

<!-- Here is an [example](https://wandb.ai/alihkw/RLDucky/runs/ijjamoqp?fbclid=IwAR0cyArbkjYi9ualpBhS_ySAGEc-TyN7DT9mNPHHkwToklf7wn2S0ubj3tA&workspace=user-) of the visualization obtained on Weights and Biases. -->

***Whats actually nice about it


## Debugger

For those using VSCode, here is a tutorial on how to set up a debugger.

click on Run And Debug(Ctrl+shift+D)

click on create a launch.json file

Delete all there is in the file and paste this instead(change the path to youre own path)

    {
       // Use IntelliSense to learn about possible attributes.
       // Hover to view descriptions of existing attributes.
       // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
       "version": "0.2.0",
       "configurations": [

           {
               "name": "Python: Current File",
               "type": "python",
               "request": "launch",
               "python": "<pathToAnacondaFile>/anaconda3/envs/mbgym/bin/python",
               // "program": "${file}",
               "module": "mbrl.examples.main",
               "args": [
                   "algorithm=planet",
                   "dynamics_model=planet",
                   "overrides=planet_duckietown"
               ],
               "console": "integratedTerminal"
           }
       ]
    }
## Typical run
To test if your CUDA works, run

    nvcc --version
    
If there is an error at this point either you debug it or you can switch to CPU by replacing "cuda:0" by "cpu" in the "/mbrl/examples/conf/main.yaml" file.

To run an experiment run:

    python -m mbrl.examples.main algorithm=planet dynamics_model=planet  overrides=planet_duckietown     
    
If you run out of memory, you can decrease the dataset size parameter in "/mbrl/example/conf/algorithm/planet.yaml". Do not reduce it under 1000 or it might fail.

## MBRL-Overview




## License
Todo

## Citing
Todo

