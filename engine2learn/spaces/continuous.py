"""
 -------------------------------------------------------------------------
 AIOpening - box.py
 
 Defines a Box like Space (Rn with upper and lower bounds)
  
 created: 2017/09/01 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""


from .base import Space
import numpy as np
import tensorflow as tf


class Continuous(Space):
    """
    A box in R^n (each coordinate is bounded)
    """

    def __init__(self, low, high, shape=None):
        """
        Three kinds of valid input:
            Continuous(0.0, 1.0) # low and high are given as scalars and shape is assumed to be ()
            Continuous(-1.0, 1.0, (3,4)) # low and high are scalars, and shape is provided
            Continuous(np.array([-1.0,-2.0]), np.array([2.0,4.0])) # low and high are arrays of the same shape (no shape given!)
        """
        self.is_scalar = False  # whether we are a single scalar (shape=())

        if shape is None:
            if isinstance(low, (int, float)) and isinstance(high, (int, float)):
                assert low < high
                self.low = float(low)
                self.high = float(high)
                self.is_scalar = True
            else:
                assert low.shape == high.shape
                self.low = low
                self.high = high
        else:
            assert np.isscalar(low) and np.isscalar(high)
            self.low = low + np.zeros(shape)
            self.high = high + np.zeros(shape)

    def sample(self, seed=None):
        if seed is not None:
            np.random.seed(seed)
        return np.random.uniform(low=self.low, high=self.high, size=None if self.is_scalar else self.low.shape)

    def contains(self, x):
        if self.is_scalar:
            return self.low <= x <= self.high
        return x.shape == self.shape and (x >= self.low).all() and (x <= self.high).all()

    @property
    def shape(self):
        if self.is_scalar:
            return tuple()
        return self.low.shape

    @property
    def flat_dim(self):
        return int(np.prod(self.shape))

    @property
    def bounds(self):
        return self.low, self.high

    def flatten(self, x):
        return np.asarray(x).flatten()

    def unflatten(self, x):
        val = np.asarray(x).reshape(self.shape)
        if self.is_scalar:
            return float(val)
        return val

    def flatten_batch(self, xs):
        xs = np.asarray(xs)
        return xs.reshape((xs.shape[0], -1))

    def unflatten_batch(self, xs):
        xs = np.asarray(xs)
        return xs.reshape((xs.shape[0],) + self.shape)

    def __repr__(self):
        return "Continuous" + str(self.shape)

    def __eq__(self, other):
        return isinstance(other, Continuous) and np.allclose(self.low, other.low) and np.allclose(self.high, other.high)

    def __hash__(self):
        return hash((self.low, self.high))

    def new_tensor_variable(self, name, extra_dims, flatten=True):
        if flatten:
            return tf.placeholder(tf.float32, shape=[None] * extra_dims + [self.flat_dim], name=name)
        return tf.placeholder(tf.float32, shape=[None] * extra_dims + list(self.shape), name=name)

    @property
    def dtype(self):
        return tf.float32
