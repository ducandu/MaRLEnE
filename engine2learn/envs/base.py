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
import collections
from cached_property import cached_property


class Env(object):
    def step(self, action):
        """
        Run one time step of the environment's dynamics. When the end of an episode is reached, reset() should be called to reset the environment's
        internal state.

        :param any action: The action to be executed by the environment. This action has to be a member of this Environment's action_space
        (a call to self.action_space.contains(action) must return True)
        :return: The observation_dict of the Environment after(!) executing the given action.
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

    def set(self, *setter_instructions):
        """
        Applies all given setter_instructions one by one to the current Environment's state.

        :param list setter_instructions: A list of instructions to be executed on this Environment object.
        :return: The observation_dict of the Environment after(!) applying all given setter_instructions.
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

    @property
    def horizon(self):
        """
        Horizon of the environment, if it has one
        """
        raise NotImplementedError

    def terminate(self):
        """
        Clean up operation,
        """
        pass

    #def get_param_values(self):
    #    return None

    #def set_param_values(self, params):
    #    pass


#class Step(collections.namedtuple("Step", ["observation", "reward", "done", "info"])):
#    def __init__(self, observation, reward, done, info):
#        super().__init__(observation=observation, reward=reward, done=done, info=info)

