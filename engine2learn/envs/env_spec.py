"""
 -------------------------------------------------------------------------
 AIOpening - envs/env_spec.py
 
 Defines a simple 2-item tuple class for action- and observation spaces.
  
 created: 2017/09/01 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""


class EnvSpec(object):

    def __init__(self, observation_space, action_space):
        """
        :param Space observation_space: The observation Space object
        :param Space action_space: the action Space object
        """
        self._observation_space = observation_space
        self._action_space = action_space

    @property
    def observation_space(self):
        return self._observation_space

    @property
    def action_space(self):
        return self._action_space