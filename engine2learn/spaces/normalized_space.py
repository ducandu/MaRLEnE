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
    def __init__(self, space, alpha=0.001, keys_to_globally_normalize=None, globally_normalize=False):
        """
        A normalized space object wraps around a "regular" space and normalizes it
        either per single value or per subspace-group (e.g. a camera image).

        :param Space space: The wrapped space to normalize.
        :param float alpha: The weight with which to weigh new incoming values for the running average
        :param Union[List[str],None] keys_to_globally_normalize: A list of keys (str) of a dict for which we do "global" normalization (not per-value)
        This is useful for images (3D continuous), which should be normalized not(!) per pixel, but per entire image.
        :param bool globally_normalize: Whether to normalize this sub-space globally (True) or per value (False)
        """
        self.space = space

        # normalized = (1-alpha)*normalized(<-old estimate) + alpha * (new observation:(mean or variance))
        self.alpha = alpha
        #self.keys_to_globally_normalize = keys_to_globally_normalize  # for Dict wrapped spaces only
        self.globally_normalize = globally_normalize  # for Continuous wrapped spaces only
        self.subspaces = None
        keys_to_globally_normalize = keys_to_globally_normalize or []

        if isinstance(space, Dict):
            self.subspaces = {}
            for key in sorted(space.keys()):
                glob_norm = True if key in keys_to_globally_normalize else False
                self.subspaces[key] = NormalizedSpace(space[key], alpha, keys_to_globally_normalize=keys_to_globally_normalize, globally_normalize=glob_norm)
        # only normalize Continuous/IntBox spaces
        elif isinstance(space, Continuous):
            if self.globally_normalize:
                self._means, self._variances = 0.0, 1.0  # single mean/var values for all dimensions of this sub-space (global normalization)
            else:
                self._means, self._variances = np.zeros(space.flat_dim), np.ones(space.flat_dim)  # single mean/var values for each(!) value in this space
        # non-normalizable spaces -> Nones
        else:
            self._means, self._variances = None, None

    # overwrite getitem to make this class subscriptable in case we wrap a dict
    def __getitem__(self, item):
        return self.subspaces[item]

    def update_stats(self, sample, flattened):
        # we are a Dict
        if self.subspaces is not None:
            n = 0
            for key in sorted(self.subspaces.keys()):
                subspace = self.subspaces[key]
                m = n + subspace.flat_dim
                subspace.update_stats(sample[key], flattened[n:m])
                n = m
        # global update mean/var (over all elements in flattened)
        elif isinstance(self._means, float):
            # TODO: terribly inefficient: fix implementation
            for single in flattened:
                self._means = (1 - self.alpha) * self._means + self.alpha * single
            for single in flattened:
                self._variances = (1 - self.alpha) * self._variances + self.alpha * np.square(single - self._means)
        # update our mean/variance running averages
        elif self._means is not None:
            self._means = (1 - self.alpha) * self._means + self.alpha * flattened
            self._variances = (1 - self.alpha) * self._variances + self.alpha * np.square(flattened - self._means)

    def normalize_sample(self, x, store_stats=True, target=True):
        """

        :param any x: The sample to be normalized.
        :param bool store_stats: Whether to store this sample in our mean/variance stats.
        :param Union[bool,any] target: The target in which to perform normalization operations.
        True: Normalize in place (in the incoming x).
        False: Return entirely new sample.
        any: Perform normalization in the given target.
        :return: The normalized sample (in the target variable).
        :rtype: any
        """
        # utilize the given sample for our stats?
        flat_x = self.flatten(x)
        if store_stats:
            self.update_stats(x, flat_x)

        # we are a Dict
        if self.subspaces is not None:
            ret = x if target is True else {} if target is False else target
            for key in sorted(self.subspaces.keys()):
                subspace = self.subspaces[key]
                sub_target = target[key] if not isinstance(target, bool) else target
                ret[key] = subspace.normalize_sample(x[key], store_stats, sub_target)
            return ret
        # we are a normalizable Space
        elif self._means is not None:
            # TODO: normalize in place? target==True
            # TODO: this should work as is with single means and var values (global normalization)
            ret = self.space.unflatten((flat_x - self._means) / (np.sqrt(self._variances) + 1e-8))
            return ret
        else:
            return x

    def rescale_sample(self, x, target=True):
        """
        Takes a normalized sample and re-scales the normalized values (0 to 1) in place.

        :param Union[dict,int,float] x: The normalized sample to be re-scaled (un-normalized).
        :param Union[bool,any] target: The target in which to perform re-scaling operations.
        True: Re-scale in place (in the incoming x).
        False: Return entirely new sample.
        any: Perform re-scaling in the given target.
        :return: The re-scaled sample (in the target variable).
        :rtype: any
        """
        # we are a dict
        if self.subspaces is not None:
            assert isinstance(x, dict)
            ret = x if target is True else {} if target is False else target
            for key, subsample in x.items():
                subspace = self.subspaces[key]
                ret[key] = subspace.rescale_sample(subsample)
            return ret

        # not a dict -> rescale single space
        if isinstance(self.space, Continuous):
            # TODO: rescale in place? target==True
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
        # right now: treat x as a non-normalized sample of the wrapped space
        return self.space.contains(x)

    def flatten(self, x, **kwargs):
        return self.space.flatten(x, **kwargs)

    def unflatten(self, x, **kwargs):
        return self.space.unflatten(x, **kwargs)

    def flatten_batch(self, xs, **kwargs):
        return self.space.flatten_batch(xs, **kwargs)

    def unflatten_batch(self, xs, **kwargs):
        return self.space.unflatten_batch(xs, **kwargs)

    @property
    def shape(self):
        return self.space.shape

    @property
    def flat_dim(self):
        return self.space.flat_dim

    def new_tensor_variable(self, name, extra_dims):
        return self.space.new_tensor_variable(name, extra_dims)
