"""
 -------------------------------------------------------------------------
 engine2learn - envs/proxy_env.py
 
 Defines a wrapper class for other Env objects for filtering purposes
 (e.g. normalization)
  
 created: 2017/10/09 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""


from .base import Env


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
