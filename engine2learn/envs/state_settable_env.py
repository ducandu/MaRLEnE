"""
 -------------------------------------------------------------------------
 engine2learn - env/state_settable_env.py
 
 A special Env, where the current state can be (force)-set manually.
  
 created: 2017/11/08 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""


from .base import Env


class StateSettableEnv(Env):
    """
    An Env that implements the set method to set the current state to some new state.
    """
    def set(self, **kwargs):
        """
        Sets the current state of the environment manually to some other state and returns a new observation.

        :param any kwargs: The set instruction(s) to be executed by the environment. A single set instruction usually set a single property of the
        state/observation vector to some new value.
        :return: The observation_dict of the Environment after(!) setting it to the new state.
        :rtype: dict
        """
        raise NotImplementedError

