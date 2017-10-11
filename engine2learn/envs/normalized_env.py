"""
 -------------------------------------------------------------------------
 engine2learn - envs/normalized_env.py
 

  
 created: 2017/10/09 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from .proxy_env import ProxyEnv
import engine2learn.spaces as spaces
from cached_property import cached_property
import numpy as np
import copy


class NormalizedEnv(ProxyEnv):
    def __init__(self, env, normalize_actions=True, sigmoid_actions=False, normalize_obs=True, alpha=0.001):
        """
        A ProxyEnv that normalizes its wrapped Env with regards to the action_space or observation_space or both.

        :param Env env: The Env to be wrapped/normalized.
        :param bool normalize_actions: Whether to normalize actions.
        :param bool sigmoid_actions: Whether normalized actions should be between 0 and 1 (default: -1 and 1)
        :param bool normalize_obs: Whether to normalize observations.
        :param float alpha: weight given to new values when calculating running averages for mean/variance of continuous samples
        """
        self.do_normalize_actions = normalize_actions
        self._sigmoid_actions = sigmoid_actions
        self.do_normalize_observations = normalize_obs

        # TODO: introduce a normalizedSpace class that takes care of normalizing any given Space
        # we can use that normalizedSpace then to squeeze through incoming non-normalized samples
        # as well as re-scale normalized samples back to non-normalized ones
        self.norm_observations = spaces.NormalizedSpace(env.observation_space, alpha=alpha)
        self.norm_actions = spaces.NormalizedSpace(env.action_space, alpha=alpha)

        super().__init__(env)

    def step(self, **kwargs):
        # TODO: make sure all Env subclasses  use this schema
        actions = kwargs.pop("mappings")  # this should be a dict of mappings

        # actions is now a dict: {"MoveForward": 1.0, "Fire": False}, a sample of a normalized Dict space
        # TODO: fix the problem that some actions may come from the NN as sigmoid/softmaxed and others as tanh (-1 to 1)
        # TODO: for now, pretend that everything comes from the network as softmaxed probability
        rescaled_actions = self.norm_actions.rescale_sample(actions)

        next_obs = self._wrapped_env.step(rescaled_actions, **kwargs)
        if self.do_normalize_observations:
            next_obs = self.norm_observations.normalize_sample(next_obs)
        return next_obs

    def reset(self):
        ret = self._wrapped_env.reset()
        if self.do_normalize_observations:
            return self.norm_observations.normalize_sample(ret)
        else:
            return ret

    """@cached_property
    def action_space(self):
        # our wrapped env has a non-normalized action space defined by the action/axis mappings in the game engine
        # action mappings are always Bool, so we don't worry about that
        # axis mappings are either Bool (only key(s) w/ scale=1.0), Discrete(3) (keys with scales=-1.0 and 1.0), or Continuous(lower, upper)
        #  (floats with different boundaries)
        # so only for axis mappings of the latter case do we have to normalize to either 0 to 1 (sigmoid) or -1 to 1 (default)
        normalized_action_space = copy.deepcopy(self._wrapped_env.action_space)
        factor = -1.0 if not self._sigmoid_actions else 0.0
        for key, space in self._wrapped_env.action_space:
            # this mapping is a continuous space -> normalize given our sigmoid option
            if isinstance(space, spaces.Continuous):
                upper_bound = np.ones(self._wrapped_env.action_space.shape)
                # overwrite with different Continuous space
                normalized_action_space[key] = spaces.Continuous(factor * upper_bound, upper_bound)
            else:
                # don't allow other Dicts in Dict
                assert isinstance(space, spaces.Discrete)
        return normalized_action_space
    """
    @property
    def action_space(self):
        return self.norm_actions

    @property
    def observation_space(self):
        return self.norm_observations

    def __str__(self):
        return "Normalized: %s" % self._wrapped_env


# create a simple handle to normalize any environment by simply calling: normalize([the Env])
normalize = NormalizedEnv

