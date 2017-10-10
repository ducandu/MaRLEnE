"""
 -------------------------------------------------------------------------
 engine2learn - spaces/normalized_space.py
 
 Defines a normalized Space where all samples of the Space are squeezed
 between -1 and 1.
 NOTE: Handles all Space sub-classes, but only really applies to
 Continuous spaces.
  
 created: 2017/10/09 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from .base import Space
from .dict import Dict
from .continuous import Continuous
import numpy as np


class NormalizedSpace(Space):
    def __init__(self, space, alpha=0.001):
        self.space = space

        # normalized = (1-alpha)*normalized(<-old estimate) + alpha * (new observation:(mean or variance))
        self.alpha = alpha
        self.subspaces = None

        if isinstance(space, Dict):
            self.subspaces = {}
            for key in sorted(space.keys()):
                self.subspaces[key] = NormalizedSpace(space[key], alpha)
        else:
            # parameters per observation space key (if Dict) that help normalize observations following the rule
            self._means, self._variances = self.init_stats(space)

    @staticmethod
    def init_stats(space):
        assert not isinstance(space, Dict)
        # only normalize Continuous spaces
        if isinstance(space, Continuous):
            # TODO: problem with first sample having to be measured against mean=0.0 (makes no sense and doesnt normalize well)
            return np.zeros(space.flat_dim), np.ones(space.flat_dim)
        # non-normalizable spaces -> return Nones
        else:
            return None, None

    def update_stats(self, sample, flattened):
        # we are a Dict
        if self.subspaces is not None:
            n = 0
            for key in sorted(self.subspaces.keys()):
                subspace = self.subspaces[key]
                m = n + subspace.flat_dim
                subspace.update_stats(sample[key], flattened[n:m])
                n = m
        # something to update -> update our mean/variance running averages
        elif self._means is not None:
            self._means = (1 - self.alpha) * self._means + self.alpha * flattened
            self._variances = (1 - self.alpha) * self._variances + self.alpha * np.square(flattened - self._means)

    def normalize_sample(self, x, store_stats=True):
        # utilize the given sample for our stats?
        flat_x = self.flatten(x)
        if store_stats:
            self.update_stats(x, flat_x)

        # we are a Dict
        if self.subspaces is not None:
            ret = {}
            for key in sorted(self.subspaces.keys()):
                subspace = self.subspaces[key]
                ret[key] = subspace.normalize_sample(x[key], store_stats)
            return ret
        # we are a normalizable Space
        elif self._means is not None:
            ret = self.space.unflatten((flat_x - self._means) / (np.sqrt(self._variances) + 1e-8))
            return ret
        else:
            return x

    def rescale_sample(self, x, sigmoid=True):
        """
        Takes a normalized sample and re-scales the normalized values (0 to 1) in place.

        :param Union[dict,int,float] x: The normalized sample to be re-scaled (un-normalized).
        :return: The re-scaled sample (in place for dict samples).
        :rtype: Union[dict,int,float]
        """
        # we are a dict
        if self.subspaces is not None:
            assert isinstance(x, dict)
            for key, subsample in x.items():
                x[key] = self.rescale_sample(subsample)
            return x  # in place

        # not a dict -> rescale single space
        if isinstance(self.space, Continuous):
            lower_bound, upper_bound = self.space.bounds
            offset = 1.0
            factor = 0.5
            # lower bound=0 upper bound=50 val=-0.5 -> rescaled val=12.5
            # 0 + (-0.5 + 1.0) * 0.5 * 50 = 12.5
            scaled_val = lower_bound + (x + offset) * factor * (upper_bound - lower_bound)
            scaled_val = np.clip(scaled_val, lower_bound, upper_bound)  # in case bounds were violated -> clip
        else:
            scaled_val = x
        return scaled_val

    def sample(self, seed=None, store_stats=False):
        return self.normalize_sample(self.space.sample(seed), store_stats)

    def contains(self, x):
        # TODO: answer question of whether x should be a normalized sample or not?
        # right now: treat x as a non-normalized sample of the wrapped space
        return self.space.contains(x)

    def flatten(self, x):
        return self.space.flatten(x)

    def unflatten(self, x):
        return self.space.unflatten(x)

    def flatten_batch(self, xs):
        return self.space.flatten_batch(xs)

    def unflatten_batch(self, xs):
        return self.space.unflatten_batch(xs)

    @property
    def shape(self):
        return self.space.shape

    @property
    def flat_dim(self):
        return self.space.flat_dim

    def new_tensor_variable(self, name, extra_dims):
        return self.space.new_tensor_variable(name, extra_dims)
