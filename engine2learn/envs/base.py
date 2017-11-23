"""
 -------------------------------------------------------------------------
 AIOpening - envs/base.py
 
 Defines the base Env class for environments.
 Comes also with an openAI Env adapter class.
  
 created: 2017/09/01 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""


from cached_property import cached_property


class EnvSpec(object):

    def __init__(self, observation_space, action_space):
        """
        :param Space observation_space: The observation Space object
        :param Space action_space: the action Space object
        """
        self._observation_space = observation_space
        self._action_space = action_space

    @cached_property
    def observation_space(self):
        return self._observation_space

    @cached_property
    def action_space(self):
        return self._action_space


class Env(object):
    def __init__(self):
        # try to keep only one copy ever of this dict and do all conversions/updates in place
        self.obs_dict = {}

    def seed(self, seed=None):
        """
        Sets the random seed of the environment to the given value (current time if None).

        :param int seed: The seed to use (current epoch seconds if None)
        """
        raise NotImplementedError

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

    @property
    def current_observation(self):
        """
        :return: Returns the current observation_dict of the Environment without actually changing anything.
        :rtype: dict
        """
        return self.obs_dict

    @cached_property
    def action_space(self):
        """
        :return: The action Space object
        :rtype: engine2learn.spaces.Space
        """
        raise NotImplementedError

    @cached_property
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

