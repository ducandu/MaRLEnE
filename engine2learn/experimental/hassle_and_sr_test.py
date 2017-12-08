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

print("done")


