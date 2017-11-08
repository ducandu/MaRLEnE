"""
 -------------------------------------------------------------------------
 AIOpening - spaces/intbox.py
 
 Defines a Box like Space of whole numbers (Zn with upper and lower bounds)
  
 created: 2017/11/03 in PyCharm
 (c) 2017/2018 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""


from .continuous import Continuous
import numpy as np


class IntBox(Continuous):
    """
    A box in Z^n (only integers; each coordinate is bounded)
    e.g. an image (w x h x RGB) where each color channel pixel can be between 0 and 255
    """
    def __init__(self, low, high, shape=None):
        """
        Three kinds of valid input:
            IntBox(0, 1) # low and high are given as scalars and shape is assumed to be ()
            IntBox(-1, 1, (3,4)) # low and high are scalars, and shape is provided
            IntBox(np.array([-1,-2]), np.array([2,4])) # low and high are arrays of the same shape (no shape given!)
        """
        if not isinstance(low, int) or not isinstance(high, int):
            assert low is None or low.shape == high.shape
        super().__init__(low, high, shape)

    def sample(self, seed=None):
        if self.has_unknown_bounds:
            raise RuntimeError("Cannot generate samples of a Space with unknown bounds. Need flatten/unflatten samples first!")
        if seed is not None:
            np.random.seed(seed)
        return np.random.uniform(self.low - 1, self.high + 1, size=None if self.is_scalar else self.low.shape).astype(int)

    def contains(self, x):
        # check for int type in given sample
        if not np.equal(np.mod(x, 1), 0).all():
            return False  # wrong type
        # let parent handle it
        return super().contains(x)

    def __repr__(self):
        return "IntBox" + str(self.shape)

    def __eq__(self, other):
        return isinstance(other, IntBox) and np.allclose(self.low, other.low) and np.allclose(self.high, other.high)


