"""
 -------------------------------------------------------------------------
 engine2learn - envs/normalized_env.py
 
 A ProxyEnv that normalizes its wrapped Env (observation_space and/or
 action_space).
  
 created: 2017/10/09 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from .proxy_env import ProxyEnv
import engine2learn.spaces as spaces
# from cached_property import cached_property
# import numpy as np
import copy


class NormalizedEnv(ProxyEnv):
    def __init__(self, env, normalize_actions=True, sigmoid_actions=False, normalize_obs=True, alpha=0.001, keys_to_globally_normalize=None):
        """
        A ProxyEnv that normalizes its wrapped Env with regards to the action_space or observation_space or both.

        :param Env env: The Env to be wrapped/normalized.
        :param bool normalize_actions: Whether to normalize actions.
        :param bool sigmoid_actions: Whether normalized actions should be between 0 and 1 (default: -1 and 1)
        :param bool normalize_obs: Whether to normalize observations.
        :param float alpha: weight given to new values when calculating running averages for mean/variance of continuous samples
        :param Union[List[str],None] keys_to_globally_normalize: A list of keys (str) of a dict for which we do "global" normalization (not per-value)
        This is useful for images (3D continuous), which should be normalized not(!) per pixel, but per entire image.
        """
        super().__init__(env)

        self.do_normalize_actions = normalize_actions
        self._sigmoid_actions = sigmoid_actions
        self.do_normalize_observations = normalize_obs

        # use NormalizedSpace to squeeze through incoming non-normalized samples
        # as well as re-scale normalized samples back to non-normalized ones
        self.norm_observations = spaces.NormalizedSpace(env.observation_space, alpha=alpha, keys_to_globally_normalize=keys_to_globally_normalize)
        if do_normalize_actions:
            self.norm_actions = spaces.NormalizedSpace(env.action_space, alpha=alpha)  # TODO: keys_to_globally_normalize
        else:
            self.norm_actions = None

        # normalize observations
        if self.do_normalize_observations:
            # overwrite our obs_dict with a copy of the wrapped one
            self.obs_dict = copy.deepcopy(self.wrapped_env.current_observation)
            self.norm_observations.normalize_sample(self.obs_dict, target=True)  # normalize in place

    def step(self, **kwargs):
        # TODO: make sure all Env subclasses use this schema
        actions = kwargs.pop("mappings")  # this should be a dict of mappings

        # actions is now a dict: {"MoveForward": 1.0, "Fire": False}, a sample of a normalized Dict space
        if self.do_normalize_actions:
            rescaled_actions = self.norm_actions.rescale_sample(actions)
            obs = self._wrapped_env.step(mappings=rescaled_actions, **kwargs)
        else:
            obs = self._wrapped_env.step(mappings=actions, **kwargs)
        
        if self.do_normalize_observations:
            # normalize in place of our own (normalized) obs_dict
            return self.norm_observations.normalize_sample(obs, target=self.obs_dict)
        else:
            return obs

    def reset(self, **kwargs):
        obs = self._wrapped_env.reset(**kwargs)
        if self.do_normalize_observations:
            return self.norm_observations.normalize_sample(obs, target=self.obs_dict)
        else:
            return obs

    @property
    def current_obs_original(self):
        return self._wrapped_env.obs_dict

    @property
    def action_space(self):
        return self.norm_actions

    @property
    def observation_space(self):
        return self.norm_observations

    def __str__(self):
        return "Normalized(%s)" % self._wrapped_env


# create a simple handle to normalize any environment by simply calling: normalize([the Env])
normalize = NormalizedEnv

