"""
 -------------------------------------------------------------------------
 AIOpening - discrete.py
 
 A discrete space with n distinct states
  
 created: 2017/09/01 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""


from .base import Space
import numpy as np
from engine2learn.misc import special
import tensorflow as tf


class Discrete(Space):
    """
    {0,1,...,n-1}
    """

    def __init__(self, n):
        self._n = n

    @property
    def n(self):
        return self._n

    def sample(self, seed=None):
        if seed is not None:
            np.random.seed(seed)
        return np.random.randint(self.n)

    def sample_n(self, n):
        return np.random.randint(low=0, high=self.n, size=n)

    def contains(self, x):
        x = np.asarray(x)
        return x.shape == () and x.dtype.kind == 'i' and x >= 0 and x < self.n

    def flatten(self, x):
        return special.to_one_hot(x, self.n)

    def unflatten(self, x):
        return special.from_one_hot(x)

    def flatten_batch(self, x):
        return special.to_one_hot_batch(x, self.n)

    def unflatten_batch(self, x):
        return special.from_one_hot_batch(x)

    @property
    def default_value(self):
        return 0

    @property
    def shape(self):
        return tuple(self.n)

    @property
    def flat_dim(self):
        return self.n

    def weighted_sample(self, weights):
        return special.weighted_sample(weights, range(self.n))

    def new_tensor_variable(self, name, extra_dims):
        # needed for safe conversion to float32
        return tf.placeholder(dtype=tf.uint8, shape=[None] * extra_dims + [self.flat_dim], name=name)

    @property
    def dtype(self):
        return tf.uint8

    def __repr__(self):
        return "Discrete({})".format(self.n)

    def __eq__(self, other):
        if not isinstance(other, Discrete):
            return False
        return self.n == other.n

    def __hash__(self):
        return hash(self.n)
