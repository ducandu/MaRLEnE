# engine2learn
Machine Learning Interface into the UE4 Game Engine.

![Python](sven1977.github.com/engine2learn/docs/images/python-logo.png)
![Spark](sven1977.github.com/engine2learn/docs/images/spark-logo.png)
![TensorFlow](sven1977.github.com/engine2learn/docs/images/tensorflow-logo.png)
![UE4](sven1977.github.com/engine2learn/docs/images/ue4-logo.png)

Connecting the Vagrant VM+Spark+Tensorflow world to the Game Dev world.

### what is engine2learn?
engine2learn is a python library as well as a UE4 plugin that - together - allow game developers and machine learning (ML) engineers
to work hand in hand by connecting a highly parallelized ML pipeline (think Spark and Tensorflow) with
any UE4 game and use that game as a reinforcement learning environment.
Our goal is to create smarter NPCs using state-of-the-art reinforcement learning (RL) methods and ML models.

The engine2learn python library provides a simple RL interface allowing algorithms to reset the game
environment (the "Env"), and then step through it (tick by tick), thereby executing different actions (called action- and axis-mappings in UE4) at
different time steps.


### the UE4 side
Game developers can use the Engine2Learn UE4 plugin to specify properties in the game, whose values are being sent to the ML
pipeline after each step (e.g. the health value of a character or enemy). Also, UE4 camera actors can be used as scene observers
such that they send their pixel recordings as 3D-tensors (w x h x RGB) after each time step back to the ML clients.
In the future, we will make audio- and sound-observations available to the ML-side as well.

Game developer need to specify a port (via the plugin's settings), on which the game will listen for incoming ML control connections.

The Engine2Learn plugin also controls automatic building/packaging/cooking procedures of ML-ready games from the UE4 Editor into the
highly parallelized ML-world (our plugin deploys one game to 100s of ML nodes automatically and starts a specified ML script).


### the python (ML) side
Once a control connection into a running game has been initiated by the ML pipeline, it can send commands to the game and use the game as
a learning environment.
The environment is represented on the python side as an engine2learn.Env object and offers the following interface for ML algorithms:

- seed: Set the random seed to some fixed value (for debugging and pseudo-random (reproducible) game play).
- reset: Set the game to its initial state.
- step: Perform a single tick (step) on the game by sending "action" information to UE4 (axis- and/or action-mappings).
The step method returns an observation (following the single step), which can be used by the ML algorithm to update a mathematical model.

### quick setup
1) Do pip install of the python engine2learn library.
```
pip install engine2learn
```

2) 


### synopsis
```python3

from engine2learn.envs.ue4_env import UE4Env
import random


if __name__ == "__main__":
    env = UE4Env(6025)  # instantiate a UE4Env (give it a port to connect to (optional 2nd arg: hostname))
    env.connect()  # connect to the UE4 game
    env.seed(10)  # set the random seed for the Env

    obs_dict = env.reset()  # reset the game to its initial state

    # specify some parameters
    num_ticks_per_step = 4  # number of ticks to perform with each step (actions will be constant throughout a single step)
    delta_time = 1 / 60  # the fake delta time to use for each tick

    for i in range(1800):
        obs_dict = env.step(delta_time=delta_time, num_ticks=num_ticks_per_step,
                            axes=("MoveRight", random.choice([-1.0, -1.0, 1.0, 1.0, 0.0])),
                            actions=("Shoot", random.choice([False, False, False, True])))

        # now use obs_dict to do some RL :)
```


### Cite

If you use Engine2Learn in your academic research, we would be grateful if you could cite it as follows:

```
@misc{mika2017engine2learn,
    author = {Mika, Sven and DeLoris, Roberto},
    title = {Engine2Learn: Bringing Deep Reinforcement Learning to the Unreal Engine 4},
    howpublished={Web page},
    url = {https://github.com/ducandu/engine2learn},
    year = {2017}
}
```


# Unreal

Having your project client compiled in your shared `/vagrant` directory, use `Vagrantfile-unreal` to start and provision the vagrant environment passing environment parameter, as in example below:

```
$ VAGRANT_VAGRANTFILE=Vagrantfile-unreal PROJECT_NAME='MyProject' vagrant up
$ VAGRANT_VAGRANTFILE=Vagrantfile-builder PROJECT_URL='https://github.com/20tab/UnrealEnginePython.git' PROJECT_NAME='UnrealEnginePython' vagrant up
``` 
