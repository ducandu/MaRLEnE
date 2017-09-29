"""
Synopsis file for the python/tensorflow/spark+UE4 project (ue42ml)

Serves the purpose of describing the most important functionalities of the API
"""

import ue42ml as ue4  # <- the lib that we would need to hook up python with UE4

from cool_ml_lib import MyPolicyNet, learn_something  # <- ducandu will code this


# get a subobject of the Env class representing the UE4 game (with the given file name) and abiding to our Env interface
game_env = ue4.create_env("CoolGame.ue4", **[some kwargs])
# alternatively: if we are a "demo" process, we can do:
#game_env = ue4.connect_ue4("servername", 8089)  # hostname, port for the "demo" connection


# initialize the game and return the first observation dict
o = game_env.reset()

# create some policy to pick actions based on observations during game play
# actions can be keyboard/mouse events that are being passed via the `step` method into the game (Env) object
policy = MyPolicyNet()  # <- ducandu will code this

while True:
    # get the next action (to-be-applied) from our policy (whatever that policy is: NN, other)
    a = policy.get_a(o)  # <- ducandu will code this

    # take one step (corresponds to one tick) in the game environment
    o_ = game_env.step(a)

    # learn something from the state (observation) transition ...
    # alternatively: if we are a "demo" process, we would skip this step
    learn_something(o, a, o_)  # <- ducandu will code this

    # do everything again .. and again .. and again
    o = o_

