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

from .remote_env import RemoteEnv
from .state_settable_env import StateSettableEnv
from engine2learn import spaces
from cached_property import cached_property
import re


class UE4Env(RemoteEnv, StateSettableEnv):
    """
    A special RemoteEnv for UE4 game connections.
    Communicates with the remote to receive information on the definitions of action- and observation spaces.
    """
    def __init__(self, port=6025, host="localhost", **kwargs):
        RemoteEnv.__init__(self, port, host)

        # TODO: remove **kwargs (unless needed for other params)
        # TODO: 20tab: get the action mappings, axis mappings, observation properties, observation cameras from the remote and leave the rest of this c'tor as is

        # list: ["Fire", "Jump", etc..] -> we don't care about the keys associated with this mapping on the UE4 side
        # all action mappings are translated to Discrete(2) (only true or false are valid values)
        self.action_space_desc = None  # kwargs.get("action_mappings")
        # dict: {"MoveForward": (-1.0, 1.0), "Mouse_X": (0.0, 1024.0)}  <-- always lower and upper bound
        # self.axis_mappings = None  # kwargs.get("axis_mappings")

        # dict: {"Character/Location/x": (-1000, 1000), "Character/Enable Gravity": bool, etc..}
        self.observation_space_desc = None  # kwargs.get("observation_properties")

        # dict: {"Cam1": (w, h, depth), "cam2": (w, h)}  # <- no depth in cam2 means grey-scale; all pixel values are between 0 and 255
        # self.observation_cameras = None  # kwargs.get("observation_cameras")

    def connect(self):
        RemoteEnv.connect(self)
        
        # get specs from our remote
        self.send({"cmd": "get_spec"})
        response = self.recv()

        # observers
        self.observation_space_desc = response["observation_space_desc"]
        # action-mappings
        self.action_space_desc = response["action_space_desc"]

        # invalidate our observation_space and action_space caches
        if "observation_space" in self.__dict__:
            del self.__dict__["observation_space"]
        if "action_space" in self.__dict__:
            del self.__dict__["action_space"]

    def set(self, setters, **kwargs):
        if "cmd" in kwargs:
            raise KeyError("Key 'cmd' must not be present in **kwargs to method `set`!")

        # forward kwargs to remote (only add command: set)
        message = kwargs
        message["cmd"] = "set"

        # sanity check setters
        # solve single tuple with prop-name and value -> should become a list (len=1) of this tuple
        if len(setters) >= 2 and not isinstance(setters[1], (list, tuple)):
            setters = list((setters,))
        for set_cmd in setters:
            assert re.match(r'\w+(:\w+)*', set_cmd[0]), "ERROR: property ({}) in setter-command does not match correct pattern!".format(set_cmd[0])
            if len(set_cmd) == 3:
                assert isinstance(set_cmd[2], bool), "ERROR: 3rd item in setter-command must be of type bool ('is_relative' flag)!"
        message["setters"] = setters

        self.send(message)
        # wait for response
        response = self.recv()
        if "obs_dict" not in response:
            raise RuntimeError("Message without field 'obs_dict' received!")
        return response["obs_dict"]

    def step(self, delta_time=1/60, num_ticks=4, actions=None, axes=None, **kwargs):
        #assert 1/600 <= delta_time < 1  # make sure our deltas are in some reasonable range
        #assert 1 <= num_ticks <= 20  # same for num_ticks
        # re-translate incoming action names into keyboard keys for the server
        try:
            if actions is None:
                actions = []
            else:
                actions = self.translate_abstract_actions_to_keys(actions)
            if axes is None:
                axes = []
            else:
                axes = self.translate_abstract_actions_to_keys(axes)
        except KeyError as e:
            raise KeyError("Action- or axis-mapping with name '{}' not defined in connected UE4 game!".format(e))

        # TODO: store the received observation in self.last_observation
        # message = {"cmd": "step", 'delta_time': 0.33,
        #     'action': [{'name': 'X', 'pressed': True}, {'name': 'Y', 'pressed': False}],
        #     'axis': [{'name': 'Left', 'delta': 1}, {'name': 'Right', 'delta': 0}]
        # }
        return RemoteEnv.step(self, delta_time=delta_time, num_ticks=num_ticks, actions=actions, axes=axes, **kwargs)

    @cached_property
    def observation_space(self):
        observation_space = {}
        # derive observation space from observation_space_desc
        if self.observation_space_desc:
            for key, desc in self.observation_space_desc.items():
                type_ = desc["type"]
                space = None

                if type_ == "bool":
                    space = spaces.Bool()
                elif type_ == "int":
                    space = spaces.IntBox(None, None, shape=() if desc["len"] == 1 else (desc["len"],))
                elif type_ == "float":
                    space = spaces.Continuous(None, None, shape=() if desc["len"] == 1 else (desc["len"],))
                elif type_ == "enum":
                    space = spaces.Discrete(desc["len"])
                elif type_ == "cam":
                    space = spaces.IntBox(0, 255, shape=desc["shape"])

                observation_space[key] = space

        return spaces.Dict(observation_space)

    @cached_property
    def action_space(self):
        action_space = {}
        # derive action space from action_space_desc
        if self.action_space_desc:
            for key, properties in self.action_space_desc.items():
                if properties["type"] == "action":
                    action_space[key] = spaces.Bool()
                else:
                    action_space[key] = spaces.Continuous(None, None)

        return spaces.Dict(action_space)

    def translate_abstract_actions_to_keys(self, abstract):
        """
        Translates a list of tuples ([pretty mapping], [value]) to a list of tuples ([some key], [translated value])
        each single item in abstract will undergo the following translation:

        Example1:
        we want: "MoveRight": 5.0
        possible keys for the action are: ("Right", 1.0), ("Left", -1.0)
        result: "Right": 5.0 * 1.0 = 5.0

        Example2:
        we want: "MoveRight": -0.5
        possible keys for the action are: ("Left", -1.0), ("Right", 1.0)
        result: "Left": -0.5 * -1.0 = 0.5 (same as "Right": -0.5)
        """

        # solve single tuple with name and value -> should become a list (len=1) of this tuple
        if len(abstract) >= 2 and not isinstance(abstract[1], (list, tuple)):
            abstract = list((abstract,))

        # now go through the list and translate each axis into an actual keyboard key (or mouse event/etc..)
        ret = []
        for a in abstract:
            # first_key = key-name (action mapping) OR tuple (key-name, scale) (axis mapping)
            #first_key = self.action_space_desc[bytes(a[0], encoding="utf-8")]["keys"][0]
            first_key = self.action_space_desc[a[0]]["keys"][0]
            # action mapping
            if isinstance(first_key, (bytes, str)):
                ret.append((first_key, a[1]))
            # axis mapping
            else:
                #ret.append((first_key[0].decode(), a[1] * first_key[1]))
                ret.append((first_key[0], a[1] * first_key[1]))

        return ret

