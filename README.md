MaRLEnE - Machine- and Reinforcement Learning ExtensioN for (game) Engines
==========================================================================

[![Docs](https://readthedocs.org/projects/engine2learn/badge)](http://engine2learn.readthedocs.io/en/latest/)


Connecting the Vagrant VM+Spark+Tensorflow world to the Game Dev world.

### What is MaRLEnE?
MaRLEnE is a UE4 plugin that allows game developers and machine learning (ML) engineers
to work hand in hand by connecting a highly parallelized ML pipeline (e.g. backed by TensorForce) with
any UE4 game and use that game as a reinforcement learning environment.
Our goal is to create smarter NPCs using state-of-the-art reinforcement learning (RL) methods and ML models.

The Plugin is supported by TensorForce, a powerful RL library interface allowing algorithms to reset the game
environment (the "Env"), and then step through it (tick by tick), thereby executing different actions (called action- and axis-mappings in UE4) at
different time steps.


### The UE4 side (Game Developers)
Game developers can use the MaRLEnE UE4 extension to specify properties in the game, whose values are being sent to the ML
pipeline after each step (e.g. the health value of a character or enemy). Also, UE4 camera actors can be used as scene observers
such that they send their pixel recordings as 3D-tensors (w x h x RGB) after each time step back to the ML clients.
In the future, we will make audio- and sound-observations available to the ML-side as well.

Game developers need to specify a port (via the plugin's settings), on which the game will listen for incoming ML control connections.

MaRLEnE also controls automatic building/packaging/cooking procedures of ML-ready games from the UE4 Editor into the
highly parallelized ML-world (our plugin deploys one game to 100s of ML nodes automatically and starts a specified ML script).


### The python side (ML engineers)
Once a control connection into a running game has been initiated by your ML pipeline (e.g. TensorForce at github.com/reinforceio/tensorforce),
it can send commands to the game and use the game as a learning environment.
The environment is represented on the python side as an Env object and offers the following interface for ML algorithms:

- seed: Set the random seed to some fixed value (for debugging and pseudo-random (reproducible) game play).
- reset: Set the game to its initial state.
- step: Perform a single tick (step) on the game by sending "action" information to UE4 (axis- and/or action-mappings).
The step method returns an observation (following the single step), which can be used by the ML algorithm to update a mathematical model.

### Quick setup
1) Get the latest UnrealEngine 4 for PC/Mac/Linux.
Go to [![UnrealEngine.com](unrealengine.com)], then download and install the latest version of UE4.


### Synopsis with TensorForce
```python3

from tensorforce.contrib.unreal_engine import unreal_engine
import random


if __name__ == "__main__":
    environment = UE4Environment(host="localhost", port=6025, connect=True, discretize_actions=True, num_ticks=6)
    environment.seed(200)

    # Do a quick random test-run with image capture of the first n images -> then exit after 1000 steps.
    # Reset the env.
    s = environment.reset()
    img_format = "RGB" if len(environment.states["shape"]) == 3 else "L"
    img = Image.fromarray(s, img_format)
    # Save first received image as a sanity-check.
    img.save("reset.png")
    for i in range(1000):
        s, is_terminal, r = environment.execute(action=random.choice(range(environment.actions["num_actions"])))
        if is_terminal:
            environment.reset()

    # now use s to do some RL :)
```


### Cite

If you use MaRLEnE in your academic research, we would be grateful if you could cite it as follows:

```
@misc{mika2017marlene,
    author = {Mika, Sven and De Ioris, Roberto},
    title = {MaRLEnE: Bringing Deep Reinforcement Learning to the Unreal Engine 4},
    howpublished={Web page},
    url = {https://github.com/ducandu/MaRLEnE},
    year = {2017}
}
```


