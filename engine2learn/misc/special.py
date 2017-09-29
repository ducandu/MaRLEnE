"""
 -------------------------------------------------------------------------
 AIOpening - special.py
 
 useful functions
  
 created: 2017/09/01 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""


import numpy as np
import tensorflow as tf


def weighted_sample(weights, objects):
    """
    Return a random item from objects, with the weighting defined by weights (which must sum to 1).
    """
    # An array of the weights, cumulatively summed.
    cs = np.cumsum(weights)
    # Find the index of the first weight over a random value.
    idx = sum(cs < np.random.rand())
    return objects[min(idx, len(objects) - 1)]


def to_one_hot(ind, dim):
    ret = np.zeros(dim)
    ret[ind] = 1
    return ret


def to_one_hot_batch(inds, dim):
    ret = np.zeros((len(inds), dim))
    ret[np.arange(len(inds)), inds] = 1
    return ret


def from_one_hot(v):
    return np.nonzero(v)[0][0]


def from_one_hot_batch(v):
    if len(v) == 0:
        return []
    return np.nonzero(v)[1]


def new_tensor(name, n_dim, dtype):
    return tf.placeholder(dtype=dtype, shape=[None] * n_dim, name=name)


