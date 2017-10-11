"""
 -------------------------------------------------------------------------
 engine2learn - envs/cam_grid_world.py
 
 A complex grid world where we observe the state via a camera and a health
 counter. The action_space consists of jump (Bool), moveforward and
 turn (both Continuous).
 This serves to test UE4-like environments with more subtle
 action- and observation_spaces.
  
 created: 2017/10/04 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from .base import Env
from .grid_world import GridWorld
from cached_property import cached_property
import numpy as np
import engine2learn.spaces as spaces


class GridWorldComplex(GridWorld):
    """
    A complex grid world where the action space is move-forward (float between -1 and 1),
    Turn (float between -1 and 1) and jump (bool).

    The state space is the same as for the simpler grid world:
    'S' : starting point
    'F' : fire: reduces health by 10% (0% means game over)
    ' ' : free space
    'W' : wall
    'H' : hole (terminates episode) (to be replaced by W in save-mode)
    'G' : goal state (terminates episode)
    """

    # add more maps to the already existing one
    GridWorld.MAPS["16x16"] = [
        "S      H        ",
        "   H       HH   ",
        "    FF   WWWWWWW",
        "  H      W      ",
        "    FF   W  H   ",
        "         W      ",
        "    FF   W      ",
        "  H          H G"
    ]

    def __init__(self, desc="4x4", save=False, reward_func="sparse"):
        # new health counter
        # gets reduced when we touch fire
        self.health0 = self.health = None
        self.orientation0 = self.orientation = 90  # 0=look up, 90=look right, 180=look down, 270=look left

        super().__init__(desc, save, reward_func)

        # placeholder for our cam return image (greyscale row x col image)
        # 255=nothing
        # 200=wall or pawn
        # 50=fire
        # 0=hole
        self.cam_pix = np.zeros(shape=(self.n_row, self.n_col), dtype=int)
        # fixed link from cam_pix into our obs_dict
        self.obs_dict["camera"] = self.cam_pix

    def reset(self):
        self.pos = self.pos0
        self.orientation = self.orientation0
        self.health = self.health0
        self.obs_dict["health"] = self.health
        self.obs_dict["_reward"] = 0
        self.obs_dict["_done"] = False
        self.update_cam_pixels()
        return self.obs_dict

    def step(self, **kwargs):
        """
        action map:
        moveForward (-1.0 (backward) 0.0 or 1.0 (Forward))
        turn (-1.0 (turn left), 0.0 or 1.0 (turn right))
        jump: jump two fields forward
        :param any kwargs: Information on how to act next.
        :return: A member of our observation_space (Dict sample).
        :rtype: dict
        """
        # first deal with manual setter instructions
        sets = kwargs.get("set")
        if sets:
            # simply set our position to some new value
            assert isinstance(sets, dict)
            for key, value in sets.items():
                assert key in ("pos", "orientation", "health")
                self.__setattr__(key, value)

        # then apply action/axis mappings
        mappings = kwargs.get("mappings")  # abide to very generic UE4Env.step interface

        # turn around (-1, 0, or 1)
        if "turn" in mappings:
            self.orientation += mappings["turn"] * 90
            self.orientation %= 360  # re-normalize orientation

        # move?
        next_pos = self.pos
        if "moveForward" in mappings:
            move = mappings["moveForward"]
            if move != 0.0:
                # classic grid world action (0=up, 1=right, 2=down, 3=left)
                if self.orientation == 0 and move == 1.0 or self.orientation == 180 and move == -1.0:
                    action = 0
                elif self.orientation == 90 and move == 1.0 or self.orientation == 270 and move == -1.0:
                    action = 1
                elif self.orientation == 0 and move == -1.0 or self.orientation == 180 and move == 1.0:
                    action = 2
                else:
                    action = 3

                possible_next_positions = self.get_possible_next_positions(self.pos, action)
                # determine the next state based on the transition function
                probs = [x[1] for x in possible_next_positions]
                next_state_idx = np.random.choice(len(probs), p=probs)
                next_pos = possible_next_positions[next_state_idx][0]

        # jump? -> move two fields forward (over walls/fires/holes w/o any damage)
        if "jump" in mappings and mappings["jump"] is True:
            # translate into classic grid world action
            action = int(self.orientation / 90)

            for i in range(2):
                possible_next_positions = self.get_possible_next_positions(next_pos, action)
                # determine the next state based on the transition function
                probs = [x[1] for x in possible_next_positions]
                next_state_idx = np.random.choice(len(probs), p=probs)
                next_pos = possible_next_positions[next_state_idx][0]

        # actually move the pawn
        self.pos = next_pos

        # determine reward and done flag
        field_type = self.desc[self.y, self.x]
        # hole
        if field_type == 'H':
            done = True
            reward = 0 if self.reward_func == "sparse" else -100
        # normal field
        elif field_type in [' ', 'S']:
            done = False
            reward = 0 if self.reward_func == "sparse" else -1
        # fire!
        elif field_type == 'F':
            done = False
            reward = 0
            self.health -= 10
            if self.health <= 0:
                done = True
                reward = 0 if self.reward_func == "sparse" else -100
                self.health = 0
        # done!
        elif field_type == 'G':
            done = True
            reward = 1
        else:
            raise NotImplementedError

        # prepare the obs_dict
        self.update_cam_pixels()
        self.obs_dict["health"] = self.health
        self.obs_dict["_reward"] = reward
        self.obs_dict["_done"] = done

        return self.obs_dict

    @cached_property
    def action_space(self):
        return spaces.Dict({"turn": spaces.Continuous(-1.0, 1.0), "moveForward": spaces.Continuous(-1.0, 1.0), "jump": spaces.Bool()})

    @cached_property
    def observation_space(self):
        return spaces.Dict({
            "camera":  spaces.Continuous(0, 255, shape=(self.n_row, self.n_col)),
            "health":  spaces.Continuous(0, 100),
            "_reward": spaces.Continuous(0, 1) if self.reward_func == "sparse" else spaces.Continuous(-100, 1),
            "_done":   spaces.Bool()
        })

    def update_cam_pixels(self):
        # 255=nothing
        # 200=wall or pawn
        # 50=fire
        # 0=hole
        map_ = {
            " ": 255,
            "X": 200,  # pawn
            "W": 200,
            "F": 50,
            "H": 0
        }
        for row in range(self.n_row):
            for col in range(self.n_col):
                field = self.desc[row, col]
                self.cam_pix[row, col] = map_[field]
        # overwrite pawn pos
        self.cam_pix[self.y, self.x] = map_["X"]
