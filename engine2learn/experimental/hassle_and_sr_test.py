"""
 -------------------------------------------------------------------------
 engine2learn - examples/hassle_and_sr_test.py
 
 Implementation of the HASSLE + Successor Representation methods for
 automatic option learning in RL.
 [1] Eigenoption Discovery through the Deep Successor Representation -
 M. Machado et al - 2017
 [2] Schmidhuber's paper
  
 created: 2017/12/04 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

import gym
import tensorflow as tf
#from engine2learn.modules import Convolutional2DModule
from engine2learn.examples.models.successor_repr_net import SuccessorReprNetwork


# first let's do SR only to reproduce results from [1]
env = gym.make("SpaceInvaders-v0")
env.reset()
#env.render()

# build tensorflow model for the SR
net = SuccessorReprNetwork("SRNet", env)

# collect 500,000 experience tuples in HDFS
for step in range(500000):
    # act uniformly randomly
    s, r, is_terminal, _ = env.step(env.action_space.sample())
    # TODO: store observations and actions on HDFS

    # if episode is over -> reset
    if is_terminal:
        env.reset()

# shuffle all experience tuples and push them through the network 10 epochs (times)
# TODO: do this with pyspark once on disk -> then read systematically from disk and train network on batches
# TODO every n steps -> update target network
net.update_target(sess)

# then produce 50,000 rows in the successor representation matrix T
env.reset()
for step in range(50000):
    # act uniformly randomly
    s, r, is_terminal, _ = env.step(env.action_space.sample())

    # if episode is over -> reset
    if is_terminal:
        env.reset()

# calculate right eigenvectors of T (e.g. first 1000)


# each eigenvector is one eigenpurpose (reward function), which can then be used via "normal" RL to learn the (eigen)option's policy



print("done")


