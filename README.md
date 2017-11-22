# engine2learn
Machine Learning Interface into the UE4 Game Engine.
Connecting the Vagrant VM+Spark+Tensorflow world to the Game Dev world.

### what is engine2learn?
engine2learn is a python library as well as a UE4 plugin that - together - allow machine learning (ML) scientists and game developers
to connect an ML pipeline (e.g. running in a VM using Spark and Tensorflow) to use any UE4 Game as a learning environment. 
The python library provides a simple reinforcement learning interface allowing agents to reset the game environment (the "env"), and then to step through it (tick by tick) setting different actions, called action- and axis-mappings in UE4, at different points in time.

### the UE4 side
Game developers can use the Engine2Learn UE4 plugin to specify properties in the game, whose values are being sent to the ML pipeline at each tick (e.g. the health value of a character or enemy). The same thing is true for UE4 Camera instances, which can be set up to send their pixel recordings to the pipeline as a 3D-tensor (w x h x RGB) at each tick.
The game developer also needs to specify a port, on which it will listen for for incoming ML control connections.

### the python (ML) side
Once a control connection has been initiated by the ML pipeline, it can send commands to the game and use it as a learning environment.
The eenvironment is represented on the python side as an Env object and offers the following interface for ML algorithms.

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


# Unreal

Having your project client compiled in your shared `/vagrant` directory, use `Vagrantfile-Unreal` to start and provision the vagrant environment passing environment parameter, as in example below:

```
$ VAGRANT_VAGRANTFILE=Vagrantfile-unreal PROJECT_NAME='MyProject' vagrant up
``` 
