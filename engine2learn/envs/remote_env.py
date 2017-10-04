"""
 -------------------------------------------------------------------------
 engine2learn - envs/remote_env.py
 
 An Environment that lives on a remote host. We communicate with this
 RemoteEnv via TCP. `step`/`reset`/etc.. are only network interfaces to
 the remote. The actual implementations and logic of these methods
 live on the remote (e.g. the UE4 game instance).
  
 created: 2017/10/04 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from .base import Env


class RemoteEnv(Env):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.last_observation = None  # cache the last observation to avoid network traffic

    def step(self, **kwargs):
        # TODO: 20tab: we need to generically just pass all data in **kwargs through the network to the remote and block(!) for an observation_dict response
        # TODO: store the received observation in self.last_observation
        # TODO: return the observation_dict
        # we are assuming local connections and fast executions (single tick). Also, we want to avoid RL-algos to have asynchronous events within themselves.
        pass

    def reset(self):
        # TODO: 20tab: same as step (no kwargs to pass), but needs to block and return observation_dict
        # TODO: store the received observation in self.last_observation
        # TODO: return the observation_dict
        pass

    def current_observation(self):
        return self.last_observation

    @property
    def action_space(self):
        # TODO: 2tab: these can be left as is (RemoteEnv is abstract class)
        raise NotImplementedError

    @property
    def observation_space(self):
        # TODO: 2tab: these can be left as is (RemoteEnv is abstract class)
        raise NotImplementedError

