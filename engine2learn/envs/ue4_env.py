"""
 -------------------------------------------------------------------------
 engine2learn - envs/ue4_simulation.py
 
 A UE4 simulating environment with UE4-typical action- and observation
 spaces that can be normalized and consist of UE4 action/axis mappings
 (actions) as well as UE4 properties and cameras (observations).
  
 created: 2017/10/03 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from .base import Env
from engine2learn import spaces
from cached_property import cached_property


class UE4Env(Env):
    def __init__(self, **kwargs):
        super().__init__()
        # list: ["Fire", "Jump", etc..] -> we don't care about the keys associated with this mapping on the UE4 side
        # all action mappings are translated to Discrete(2) (only true or false are valid values)
        self.action_mappings = kwargs.get("action_mappings")

        # dict: {"MoveForward": (-1.0, 1.0), "Mouse_X": (0.0, 1024.0)}  <-- always lower and upper bound
        self.axis_mappings = kwargs.get("axis_mappings")

        # dict: {"Character/Location/x": (-1000, 1000), "Character/Enable Gravity": bool, etc..}
        self.observation_properties = kwargs.get("observation_properties")
        # dict: {"Cam1": (w, h, depth), "cam2": (w, h)}  # <- no depth in cam2 means grey-scale; all pixel values are between 0 and 255
        self.observation_cameras = kwargs.get("observation_cameras")

    def step(self, **kwargs):
        return NotImplementedError

    def reset(self):
        return NotImplementedError

    def current_observation(self):
        return NotImplementedError

    @cached_property
    def observation_space(self):
        # derive observation space from observation_properties and observation_cameras
        observation_space = {}
        # do the UE4 (actors') properties
        for prop, spec in self.observation_properties:
            if isinstance(spec, tuple):
                assert len(spec) == 2
                observation_space[prop] = spaces.Continuous(spec[0], spec[1])
            else:
                assert spec == bool
                observation_space[prop] = spaces.Discrete(2)
        # do the cameras
        for camera, spec in self.observation_cameras:
            assert camera not in observation_space
            assert 2 <= len(spec) <= 3
            shape = [spec[0], spec[1]]
            # add color depth?
            if len(spec) == 3:
                shape.append(spec[2])
            observation_space[camera] = spaces.Continuous(0, 255, shape=shape)

        return spaces.Dict(observation_space)

    @cached_property
    def action_space(self):
        # derive action space from action_mappings and axis_mappings
        action_space = {}
        for name in self.action_mappings:
            action_space[name] = spaces.Discrete(2)
        for name, bounds in self.axis_mappings.items():
            assert name not in action_space
            assert isinstance(bounds, tuple) and len(bounds) == 2
            action_space[name] = spaces.Continuous(bounds[0], bounds[1])

        return spaces.Dict(action_space)


