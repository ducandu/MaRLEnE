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
import random
from engine2learn.misc import special
import tensorflow as tf


class Discrete(Space):
    """
    {0,1,...,n-1}
    """

    def __init__(self, n, is_distribution=False):
        assert n > 2, "ERROR: spaces.Discrete's number of states has to be larger than 2. Use spaces.Bool() for n=2."
        self._n = n
        # whether a flattened sample represents a probability distribution from which to sample the actual discrete value
        self.is_distribution = is_distribution

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
        return x.shape == () and x.dtype.kind == 'i' and 0 <= x < self.n

    def flatten(self, x):
        assert self.contains(x)
        return special.to_one_hot(x, self.n)

    def unflatten(self, x):
        if self.is_distribution:
            return np.random.choice(np.arange(self.n), p=x)
        return special.from_one_hot(x)

    def flatten_batch(self, x):
        return special.to_one_hot_batch(x, self.n)

    def unflatten_batch(self, x):
        if self.is_distribution:
            return np.array([np.random.choice(np.arange(self.n), p=dist) for dist in x])
        return special.from_one_hot_batch(x)

    @property
    def default_value(self):
        return 0

    @property
    def shape(self):
        return tuple((self.n,))

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


class Bool(Discrete):
    """
    A Bool space is a special case of Discrete where n=2, the possible values are True or False,
    and the flattened representation is a 1D vector of dim=1 ([0]=False or [1]=True)
    """
    def __init__(self):
        super().__init__(3)
        self._n = 2  # circumvent the assertion inside Discrete for n <= 2

    def sample(self, seed=None):
        if seed is not None:
            random.seed(seed)
        return not not random.getrandbits(1)  # fastest way (better than bool)

    def sample_n(self, n):
        return np.random.randint(low=0, high=2, size=n, dtype=bool)

    def contains(self, x):
        return isinstance(x, bool)

    def flatten(self, x):
        # special case: only two possible states (bool) -> make it just 1D vector with one element with values either 0 or 1
        assert self.contains(x), "ERROR: Bool space does not contain sample {}".format(x)
        return np.zeros(1) if not x else np.ones(1)  # x can only be 0 or 1 (only two states)

    def unflatten(self, x):
        return x[0] == 1

    def flatten_batch(self, x):
        return np.array([[np.zeros(1) if not i else np.ones(1)] for i in x])

    def unflatten_batch(self, x):
        return np.array([True if i[0] == 1 else False for i in x])

    @property
    def default_value(self):
        return False

    @property
    def shape(self):
        return tuple()

    @property
    def flat_dim(self):
        return 1

    def __repr__(self):
        return "Bool()"
