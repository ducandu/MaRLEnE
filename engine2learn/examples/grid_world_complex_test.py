"""
 -------------------------------------------------------------------------
 engine2learn - examples/grid_world_complex_test.py
 
 Example use case for a GridWorldComplex Env.
  
 created: 2017/10/10 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from engine2learn.envs import GridWorldComplex, normalize
import random


# create a save grid-world without holes
game = GridWorldComplex("16x16", save=False, reward_func="rich_potential")
game = normalize(game, keys_to_globally_normalize=["camera"])
# game is now an Env-interfaced object

print("shape of normalized: {}".format(game.observation_space["camera"].shape))

# reset the game
obs_dict = game.reset()  # type: dict
game.render()

# The observation_dict has two "special" keys: _done and _reward that can be used for reinforcement learning algorithms.
# - these special fields are not a requirement for any Env (game) objects to return in the observation_dict

#action: moveForward=-1 turn=0 jump=True
#action: moveForward=0 turn=0 jump=False
#action: moveForward=-1 turn=0 jump=False
#action: moveForward=-1 turn=0 jump=False
#action: moveForward=-1 turn=0 jump=True
#action: moveForward=-1 turn=0 jump=False
#action: moveForward=0 turn=0 jump=False
#action: moveForward=1 turn=0 jump=False
#action: moveForward=1 turn=0 jump=True
#action: moveForward=0 turn=0 jump=True

"""mappings = {
    0: {"turn": 0, "moveForward": -1, "jump": True},
    1: {"turn": 0, "moveForward": 0, "jump": False},
    2: {"turn": 0, "moveForward": -1, "jump": False},
    3: {"turn": 0, "moveForward": -1, "jump": False},
    4: {"turn": 0, "moveForward": -1, "jump": True},
    5: {"turn": 0, "moveForward": -1, "jump": False},
    6: {"turn": 0, "moveForward": 0, "jump": False},
    7: {"turn": 0, "moveForward": 1, "jump": False},
    8: {"turn": 0, "moveForward": 1, "jump": True},
    9: {"turn": 0, "moveForward": 0, "jump": True}
}
"""

x = 0
while not obs_dict["_done"]:

    # pick random action mapping (do not do any learning in this script)
    mapping = {"turn": random.choice([-1.0, 0.0, 1.0]), "moveForward": random.choice([-1.0, 0.0, 1.0]), "jump": random.choice([False, True])}
    #mapping = mappings[x]
    print("action-mapping={}".format(mapping))

    obs_dict = game.step(mappings=mapping)
    game.render()
    x += 1

# did we receive a last positive reward? if yes -> we won
if obs_dict["_reward"] > 0:
    print("You Won!")
# we lost
else:
    print("Game Over!")
    print("at very end: _done={} _reward={} pos={} ({},{}) orient={}".format(obs_dict["_done"], obs_dict["_reward"], game._wrapped_env.pos, game._wrapped_env.x, game._wrapped_env.y, obs_dict["orientation"]))
    obs_dict = game.reset()
    game.render()
    print("after reset: _done={} _reward={} pos={} ({},{}) orient={}".format(obs_dict["_done"], obs_dict["_reward"], game._wrapped_env.pos, game._wrapped_env.x, game._wrapped_env.y, obs_dict["orientation"]))
