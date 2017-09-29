from engine2learn.envs import GridWorld
import random

# create a save grid-world without holes
game = GridWorld("4x4", save=True)
# game is now an Env-interfaced object


# reset the game
game.reset()

# test the set method (move to pos=1, which translates to x=0, y=1)
obs_dict = game.set(1)

# The observation_dict has two "special" keys: _done and _reward that can be used for reinforcement learning algorithms.
# - these special fields are not a requirement for any Env (game) objects to return in the observation_dict
while not obs_dict["_done"]:
    game.render()  # some Envs implement this method

    # pick random action (do not do any learning in this script)
    a = random.choice(range(game.action_dim))
    print("action={}".format("left" if a == 0 else "down" if a == 1 else "right" if a == 2 else "up"))

    obs_dict = game.step(a)  # apply the action to the Env and  retrieve the next observation_dict

# did we receive a reward? if yes -> we won
if obs_dict["_reward"] > 0:
    print("You Won!")
# we lost
else:
    print("Game Over!")
