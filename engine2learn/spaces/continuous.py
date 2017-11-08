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
from cached_property import cached_property


class Continuous(Space):
    """
    A box in R^n (each coordinate is bounded)
    """

    def __init__(self, low, high, shape=None):
        """
        Valid inputs:
            Continuous(0.0, 1.0) # low and high are given as scalars and shape is assumed to be () -> single scalar between low and high
            Continuous(-1.0, 1.0, (3,4)) # low and high are scalars, and shape is provided -> nD array all(!) between low and high
            Continuous(np.array([-1.0,-2.0]), np.array([2.0,4.0])) # low and high are arrays of the same shape (no shape given!) -> nD array where each dimension has different bounds
            Continuous(None, None, (2,3,4)) # low and high are not given (unknown) -> figure out bounds by observing incoming samples (use flatten(_batch)? and unflatten(_batch)? methods to get samples)
        """
        self.is_scalar = False  # whether we are a single scalar (shape=())
        self.has_unknown_bounds = False
        self.has_flex_bounds = False

        if shape is None:
            if isinstance(low, (int, float)) and isinstance(high, (int, float)):
                assert low < high
                self.low = float(low)
                self.high = float(high)
                self.is_scalar = True
            elif low is None:
                assert high is None
                self.has_unknown_bounds = True
                self.has_flex_bounds = True
                self.is_scalar = True
                self.low = float("inf")
                self.high = float("-inf")
            else:
                assert low.shape == high.shape
                self.low = low
                self.high = high
        else:
            if low is None:
                assert high is None
                self.has_unknown_bounds = True
                self.has_flex_bounds = True
                self.low = np.zeros(shape)
                self.high = np.zeros(shape)                
            else:
                assert np.isscalar(low) and np.isscalar(high)
                self.low = low + np.zeros(shape)
                self.high = high + np.zeros(shape)

    def sample(self, seed=None):
        if self.has_unknown_bounds:
            raise RuntimeError("Cannot generate samples of a Space with unknown bounds. Need flatten/unflatten samples first!")
        if seed is not None:
            np.random.seed(seed)
        return np.random.uniform(low=self.low, high=self.high, size=None if self.is_scalar else self.low.shape)

    def contains(self, x):
        if self.has_unknown_bounds:
            raise RuntimeError("Cannot check whether Space with unknown bounds contains sample. Need flatten/unflatten samples first!")
        if self.is_scalar:
            return self.low <= x <= self.high
        return x.shape == self.shape and (x >= self.low).all() and (x <= self.high).all()

    @cached_property
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

    def flatten(self, x, **kwargs):
        # update our flexible bounds
        # TODO: after n samples, only recalc bounds every m samples
        if self.has_flex_bounds:
            self.has_unknown_bounds = False
            if self.is_scalar:
                self.low = np.minimum(self.low, x, out=None)
                self.high = np.maximum(self.high, x, out=None)
            else:
                np.minimum(self.low, x, out=self.low)
                np.maximum(self.high, x, out=self.high)

        return np.asarray(x).flatten()

    def unflatten(self, x, **kwargs):
        val = np.asarray(x).reshape(self.shape)

        # update our flexible bounds
        # TODO: after n samples, only recalc bounds every m samples
        if self.has_flex_bounds:
            self.has_unknown_bounds = False
            if self.is_scalar:
                self.low = np.minimum(self.low, val, out=None)
                self.high = np.maximum(self.high, val, out=None)
            else:
                np.minimum(self.low, val, out=self.low)
                np.maximum(self.high, val, out=self.high)

        if self.is_scalar:
            return float(val)
        return val

    def flatten_batch(self, xs, **kwargs):
        xs = np.asarray(xs)
        # update our flexible bounds
        # TODO: after n samples, only recalc bounds every m samples
        if self.has_flex_bounds:
            self.has_unknown_bounds = False
            for x in xs:
                np.minimum(self.low, x, out=self.low)
                np.maximum(self.high, x, out=self.high)

        return xs.reshape((xs.shape[0], -1))

    def unflatten_batch(self, xs, **kwargs):
        xs = np.asarray(xs)
        xs = xs.reshape((xs.shape[0],) + self.shape)

        # update our flexible bounds
        # TODO: after n samples, only recalc bounds every m samples
        if self.has_flex_bounds:
            self.has_unknown_bounds = False
            for x in xs:
                np.minimum(self.low, x, out=self.low)
                np.maximum(self.high, x, out=self.high)

        return xs

    def __repr__(self):
        return "Continuous" + str(self.shape)

    def __eq__(self, other):
        return isinstance(other, Continuous) and np.allclose(self.low, other.low) and np.allclose(self.high, other.high)

    # TODO: for flexible bounds, this is probably a bad idea b/c low and high will change all the time
    def __hash__(self):
        return hash((self.low, self.high))

    def new_tensor_variable(self, name, extra_dims, flatten=True):
        if flatten:
            return tf.placeholder(tf.float32, shape=[None] * extra_dims + [self.flat_dim], name=name)
        return tf.placeholder(tf.float32, shape=[None] * extra_dims + list(self.shape), name=name)

    @property
    def dtype(self):
        return tf.float32

