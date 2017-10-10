"""
 -------------------------------------------------------------------------
 AIOpening - dict.py

 A Dict space (a keyed combination of n other spaces)

 created: 2017/09/01 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from .base import Space
import numpy as np
from engine2learn.misc import special


class Dict(Space, dict):
    def __init__(self, d, **kwargs):
        # make sure all values in the given dict are actually other Space objects
        assert all(isinstance(v, Space) for v in d.values())
        dict.__init__(self, d)
        dtypes = [c.new_tensor_variable("tmp", extra_dims=0).dtype for c in self.values()]
        if len(dtypes) > 0 and hasattr(dtypes[0], "as_numpy_dtype"):
            dtypes = [d.as_numpy_dtype for d in dtypes]
        self._common_dtype = np.core.numerictypes.find_common_type([], dtypes)

    def sample(self, seed=None):
        if seed is not None:
            np.random.seed(seed)
        return dict({key: subspace.sample() for key, subspace in self.items()})

    def contains(self, x):
        return isinstance(x, dict) and all(self[key].contains(x[key]) for key in self.keys())

    def new_tensor_variable(self, name, extra_dims):
        return special.new_tensor(name=name, n_dim=extra_dims + 1, dtype=self._common_dtype)

    @property
    def flat_dim(self):
        return int(np.sum([c.flat_dim for c in self.values()]))

    @property
    def shape(self):
        # TODO: there may be a problem with this if we have a Dict space inside this Dict
        return tuple([self[key].flat_dim for key in sorted(self.keys())])

    def flatten(self, x):
        return np.concatenate([self[key].flatten(x[key]) for key in sorted(self.keys())])

    def flatten_batch(self, xs):
        # xs = [ {1st sample}, {2nd sample}, {3rd sample}, ...]
        xs_regrouped = {key: [d[key] for d in xs] for key in sorted(xs[0].keys())}
        # xs_regrouped = { key0: [1st[key0], 2nd[key0], 3rd[key0] ...], key1: [], etc...]
        flat_regrouped = [self[key].flatten_batch(xs_regrouped[key]) for key in sorted(self.keys())]
        return np.concatenate(flat_regrouped, axis=-1)

    def unflatten(self, x):
        dims = [self[key].flat_dim for key in sorted(self.keys())]
        flat_xs = np.split(x, np.cumsum(dims)[:-1])
        return {key: self[key].unflatten(flat_xs[i]) for i, key in enumerate(sorted(self.keys()))}

    def unflatten_batch(self, xs):
        # dims = [self[key].flat_dim for key in sorted(self.keys())]
        # flat_xs = np.split(xs, np.cumsum(dims)[:-1], axis=-1)
        # unflattened_xs = [c.unflatten_n(xi) for c, xi in zip(self.components, flat_xs)]
        # #unflattened_xs_grouped = list(zip(*unflattened_xs))
        # return unflattened_xs_grouped
        # TODO: this may not be the fastest way to do this, but a simple one
        return np.array([self.unflatten(sample) for sample in xs])

    def __eq__(self, other):
        if not isinstance(other, Dict):
            return False
        return dict(self) == dict(other)

    def __repr__(self):
        return "Dict({})".format({key: self[key].__repr__() for key in self.keys()})

    def __hash__(self):
        return hash(tuple(sorted(self.keys())))