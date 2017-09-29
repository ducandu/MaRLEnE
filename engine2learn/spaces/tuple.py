"""
 -------------------------------------------------------------------------
 AIOpening - tuple.py

 A Tuple space (a combination of n other spaces)

 created: 2017/09/01 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from .base import Space
import numpy as np
from engine2learn.misc import special


class Tuple(Space):
    def __init__(self, *components):
        if isinstance(components[0], (list, tuple)):
            assert len(components) == 1
            components = components[0]
        self._components = tuple(components)
        dtypes = [c.new_tensor_variable("tmp", extra_dims=0).dtype for c in components]
        if len(dtypes) > 0 and hasattr(dtypes[0], "as_numpy_dtype"):
            dtypes = [d.as_numpy_dtype for d in dtypes]
        self._common_dtype = np.core.numerictypes.find_common_type([], dtypes)

    def sample(self, seed=None):
        if seed is not None:
            np.random.seed(seed)
        return tuple(x.sample() for x in self._components)

    @property
    def components(self):
        return self._components

    def contains(self, x):
        return isinstance(x, tuple) and all(c.contains(xi) for c, xi in zip(self._components, x))

    def new_tensor_variable(self, name, extra_dims):
        return special.new_tensor(name=name, n_dim=extra_dims + 1, dtype=self._common_dtype)

    @property
    def flat_dim(self):
        return np.sum([c.flat_dim for c in self._components])

    @property
    def shape(self):
        return tuple([c.flat_dim for c in self._components])

    def flatten(self, x):
        return np.concatenate([c.flatten(xi) for c, xi in zip(self._components, x)])

    def flatten_batch(self, xs):
        xs_regrouped = [[x[i] for x in xs] for i in range(len(xs[0]))]
        flat_regrouped = [c.flatten_batch(xi) for c, xi in zip(self.components, xs_regrouped)]
        return np.concatenate(flat_regrouped, axis=-1)

    def unflatten(self, x):
        dims = [c.flat_dim for c in self._components]
        flat_xs = np.split(x, np.cumsum(dims)[:-1])
        return tuple(c.unflatten(xi) for c, xi in zip(self._components, flat_xs))

    def unflatten_batch(self, xs):
        dims = [c.flat_dim for c in self._components]
        flat_xs = np.split(xs, np.cumsum(dims)[:-1], axis=-1)
        unflattened_xs = [c.unflatten_n(xi) for c, xi in zip(self.components, flat_xs)]
        unflattened_xs_grouped = list(zip(*unflattened_xs))
        return unflattened_xs_grouped

    def __eq__(self, other):
        if not isinstance(other, Tuple):
            return False
        return tuple(self.components) == tuple(other.components)

    def __repr__(self):
        return "Tuple({})".format(tuple([cmp.__repr__() for cmp in self._components]))

    def __hash__(self):
        return hash(tuple(self.components))