"""
 -------------------------------------------------------------------------
 AIOpening - envs/base.py
 
 Defines the base Env class for environments.
 Comes also with an openAI Env adapter class.
  
 created: 2017/09/01 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""


from .env_spec import EnvSpec
from cached_property import cached_property
import numpy as np
from engine2learn.spaces import Discrete, Continuous, Dict
import copy


class Env(object):
    def step(self, **kwargs):
        """
        Run one time step of the environment's dynamics. When the end of an episode is reached, reset() should be called to reset the environment's
        internal state.

        :param any kwargs: The action(s) to be executed by the environment. Actions have to be members of this Environment's action_space
        (a call to self.action_space.contains(action) must return True)
        :return: The observation_dict of the Environment after(!) executing the given actions(s).
        :rtype: dict
        """
        raise NotImplementedError

    def reset(self):
        """
        Resets the state of the environment, returning an initial observation.

        :return: The initial observation_dict of the Environment.
        :rtype: dict
        """
        raise NotImplementedError

    def current_observation(self):
        """
        :return: Returns the current observation_dict of the Environment without actually changing anything.
        :rtype: dict
        """
        raise NotImplementedError

    @property
    def action_space(self):
        """
        :return: The action Space object
        :rtype: engine2learn.spaces.Space
        """
        raise NotImplementedError

    @property
    def observation_space(self):
        """
        :return: The observation Space object
        :rtype: engine2learn.spaces.Space
        """
        raise NotImplementedError

    # Helpers that derive from Spaces
    @property
    def action_dim(self):
        return self.action_space.flat_dim

    def render(self):
        """
        Should render the Environment in its current state. May be implemented or not.
        """
        pass

    #def log_diagnostics(self, paths):
    #    """
    #    Log extra information per iteration based on the collected paths
    #    """
    #    pass

    @cached_property
    def spec(self):
        """
        A simple wrapper for our action_space and observation_space Space definitions.

        :return: An EnvSpec Object wrapping our action_space and observation_space.
        :rtype: EnvSpec
        """
        return EnvSpec(observation_space=self.observation_space, action_space=self.action_space)

    #@property
    #def horizon(self):
    #    """
    #    Horizon of the environment, if it has one
    #    """
    #    raise NotImplementedError

    def terminate(self):
        """
        Clean up operation,
        """
        pass


class ProxyEnv(Env):
    """
    A simple wrapper class wrapping around another (core) environment. Useful for filtering purposes
    e.g. normalization.
    """
    def __init__(self, wrapped_env):
        self._wrapped_env = wrapped_env

    @property
    def wrapped_env(self):
        return self._wrapped_env

    def step(self, **kwargs):
        return self._wrapped_env.step(**kwargs)

    def reset(self, **kwargs):
        return self._wrapped_env.reset(**kwargs)

    def current_observation(self):
        return self._wrapped_env.current_observation()

    @property
    def action_space(self):
        return self._wrapped_env.action_space

    @property
    def action_dim(self):
        return self._wrapped_env.action_space.flat_dim

    @property
    def observation_space(self):
        return self._wrapped_env.observation_space

    def render(self, *args, **kwargs):
        return self._wrapped_env.render(*args, **kwargs)

    #@property
    #def horizon(self):
    #    return self._wrapped_env.horizon

    def terminate(self):
        self._wrapped_env.terminate()


class NormalizedEnv(ProxyEnv):
    def __init__(self, env, normalize_actions=True, sigmoid_actions=False, normalize_obs=True, obs_alpha=0.001):
        """
        A ProxyEnv that normalizes its wrapped Env with regards to the action_space or observation_space or both.

        :param Env env: The Env to be wrapped/normalized.
        :param bool normalize_actions: Whether to normalize actions.
        :param bool sigmoid_actions: Whether normalized actions should be between 0 and 1 (default: -1 and 1)
        :param bool normalize_obs: Whether to normalize observations.
        :param float obs_alpha: ??? TODO:
        """
        assert isinstance(env.action_space, Dict)
        super().__init__(env)
        self._normalize_actions = normalize_actions
        self._sigmoid_actions = sigmoid_actions
        self._normalize_obs = normalize_obs
        self._obs_alpha = obs_alpha
        self._obs_mean = np.zeros(env.observation_space.flat_dim)
        self._obs_var = np.ones(env.observation_space.flat_dim)

    @staticmethod
    def rescale_actions(actions, space, sigmoid=False):
        """
        Takes normalized actions, a dict of key/value pairs, whose keys smust be found in given space (which is a spaces.Dict)
        and re-scale the normalized values (0 to 1 if sigmoid is True, or -1 to 1) in place.

        :param dict actions: A dictionary of values (members of a space) to be normalized.
        :param spaces.Dict space: The spaces.Dict space to use (defines the boundaries).
        :param bool sigmoid: Whether the incoming actions are between 0 and 1 (sigmoid), or -1 and 1, which is the default.
        :return: The normalized values dict.
        :rtype: dict
        """
        assert isinstance(actions, dict)
        assert isinstance(space, Dict)

        offset = 1.0 if not sigmoid else 0.0
        factor = 0.5 if not sigmoid else 1.0

        for key, val in actions.items():
            assert key in space
            if isinstance(space[key], Continuous):
                lower_bound, upper_bound = space[key].bounds
                # lower bound=0 upper bound=50 val=0.5 sigmoid==True -> rescaled val=25
                # 0 + (0.5 + 0.0) * 1.0 * 50 = 25
                scaled_val = lower_bound + (val + offset) * factor * (upper_bound - lower_bound)
                scaled_val = np.clip(scaled_val, lower_bound, upper_bound)  # in case bounds were violated -> clip
            else:
                scaled_val = val

            # normalize in place
            actions[key] = scaled_val

    def step(self, **kwargs):
        # TODO: make sure all Env subclasses  use this schema
        actions = kwargs.get("mappings")  # this should be a dict of mappings
        # actions is now a dict: {"MoveForward": 1.0, "Fire": 0}
        # TODO: fix the problem that some actions may come from the NN as sigmoid/softmaxed and others as tanh (-1 to 1)
        # TODO: for now, pretend that everything comes from the network as softmaxed probability
        rescaled_action = self.rescale_actions(actions, self._wrapped_env.action_space, sigmoid=True)
        next_obs = self._wrapped_env.step(rescaled_action)
        if self._normalize_obs:
            next_obs = self._apply_normalize_obs(next_obs)
        return next_obs

    def reset(self):
        ret = self._wrapped_env.reset()
        if self._normalize_obs:
            return self._apply_normalize_obs(ret)
        else:
            return ret

    def _update_obs_estimate(self, obs):
        flat_obs = self.wrapped_env.observation_space.flatten(obs)
        self._obs_mean = (1 - self._obs_alpha) * self._obs_mean + self._obs_alpha * flat_obs
        self._obs_var = (1 - self._obs_alpha) * self._obs_var + self._obs_alpha * np.square(flat_obs - self._obs_mean)

    def _apply_normalize_obs(self, obs):
        self._update_obs_estimate(obs)
        return (obs - self._obs_mean) / (np.sqrt(self._obs_var) + 1e-8)

    #def __getstate__(self):
    #    d = Serializable.__getstate__(self) ??
    #    d["_obs_mean"] = self._obs_mean
    #    d["_obs_var"] = self._obs_var
    #    return d

    #def __setstate__(self, d):
    #    self._obs_mean = d["_obs_mean"]
    #    self._obs_var = d["_obs_var"]

    @cached_property
    def action_space(self):
        # our wrapped env has a non-normalized action space defined by the action/axis mappings in the game engine
        # action mappings are always Discrete(2), so we don't worry about that
        # axis mappings are either Discrete(2) (only key(s) w/ scale=1.0), Discrete(3) (keys with scales=-1.0 and 1.0), or Continuous(lower, upper)
        #  (floats with different boundaries)
        # so only for axis mappings of the latter case do we have to normalize to either 0 to 1 (sigmoid) or -1 to 1 (default)
        normalized_action_space = copy.deepcopy(self._wrapped_env.action_space)
        factor = -1.0 if not self._sigmoid_actions else 0.0
        for key, space in self._wrapped_env.action_space:
            # this mapping is a continuous space -> normalize given our sigmoid option
            if isinstance(space, Continuous):
                upper_bound = np.ones(self._wrapped_env.action_space.shape)
                # overwrite with different Continuous space
                normalized_action_space[key] = Continuous(factor * upper_bound, upper_bound)
            else:
                # don't allow other Dicts in Dict
                assert isinstance(space, Discrete)
        return normalized_action_space

    def __str__(self):
        return "Normalized: %s" % self._wrapped_env


# create a simple handle to normalize any environment by simply calling: normalize([the Env])
normalize = NormalizedEnv

