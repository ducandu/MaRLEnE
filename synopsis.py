"""
Synopsis file for the python/tensorflow/spark+UE4 project (engine2learn)

Serves the purpose of describing the most important functionalities of the API
"""

import engine2learn  # <- the lib that we would need to hook up python with UE4

from cool_ml_lib import MyPolicyNet, learn_something  # <- ducandu will code this


# get an Env object representing the UE4 game (with the given file name) and abiding to our Env interface
game_env = engine2learn.connect_env("ue4", "CoolGame.ue4", **[some kwargs])

# initialize the game and return the first observation dict
o = game_env.reset()

# create some policy to pick actions based on observations during game play
# actions can be keyboard/mouse events that are being passed via the `step` method into the game (Env) object
policy = MyPolicyNet()  # <- ducandu will code this

while True:
    # get the next action (to-be-applied) from our policy (whatever that policy is: NN, other)
    a = policy.get_a(o)  # <- ducandu will code this

    # take one step (corresponds to one tick) in the game environment
    o_ = game_env.step(mappings={"MoveForward": 1.0, "Fire": True}, num_ticks=1)

    # learn something from the state (observation) transition ...
    # alternatively: if we are a "demo" process, we would skip this step
    learn_something(o, a, o_)  # <- ducandu will code this

    # do everything again .. and again .. and again
    o = o_

