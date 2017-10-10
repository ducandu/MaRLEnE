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

    def reset(self):
        self.pos = self.pos0
        self.orientation = self.orientation0
        self.health = self.health0
        self.obs_dict["camera"] = TODO: create a top-down 'image' of the env
        self.obs_dict["health"] = self.health
        self.obs_dict["_reward"] = 0
        self.obs_dict["_done"] = False
        return self.obs_dict

    def step(self, **kwargs):
        """
        action map:
        moveForward (-1.0 (backward) 0.0 or 1.0 (Forward))
        turn (-1.0 (turn left), 0.0 or 1.0 (turn right))
        jump: jump two fields forward
        :param any kwargs: Information on how to act next.
        action (int): An integer 0-3 that describes the next action.
        set (List[int]): A list of integers to set the current position to before acting.
        :return: A member of our observation_space (Dict sample).
        :rtype: dict
        """
        # first deal with manual setter instructions
        sets = kwargs.get("set")
        if sets:
            # simply set our position to some new value
            for instruction in sets:
                assert isinstance(instruction, int) and 0 <= instruction < self.observation_space["pos"].flat_dim
                self.pos = instruction

        # then perform an action
        action = kwargs.get("action", 0)  # abide to very generic Env.step interface
        possible_next_positions = self.get_possible_next_positions(self.pos, action)
        # determine the next state based on the transition function
        probs = [x[1] for x in possible_next_positions]
        next_state_idx = np.random.choice(len(probs), p=probs)
        next_pos = possible_next_positions[next_state_idx][0]

        next_x = next_pos // self.n_col
        next_y = next_pos % self.n_col

        # determine reward and done flag
        next_state_type = self.desc[next_y, next_x]
        if next_state_type == 'H':
            done = True
            reward = 0 if self.reward_func == "sparse" else -100
        elif next_state_type in ['F', 'S']:
            done = False
            reward = 0 if self.reward_func == "sparse" else -1
        elif next_state_type == 'G':
            done = True
            reward = 1
        else:
            raise NotImplementedError

        # prepare the obs_dict
        self.obs_dict["pos"] = self.pos = next_pos
        self.obs_dict["_reward"] = reward
        self.obs_dict["_done"] = done

        return self.obs_dict

    def get_possible_next_positions(self, pos, action):
        """
        Given the pos and action, return a list of possible next states and their probabilities. Only next states
        with nonzero probabilities will be returned
        For now: Implemented as a deterministic MDP

        :param pos: current position
        :param action: action
        :return: a list of pairs (pos', p(pos'|pos,a))
        """
        # assert self.observation_space.contains(pos)
        # assert self.action_space.contains(action)

        x = pos // self.n_col
        y = pos % self.n_col
        coords = np.array([x, y])

        increments = np.array([[-1, 0], [0, 1], [1, 0], [0, -1]])
        next_coords = np.clip(
            coords + increments[action],
            [0, 0],
            [self.n_row - 1, self.n_col - 1]
        )
        next_pos = next_coords[0] * self.n_col + next_coords[1]
        pos_type = self.desc[y, x]
        next_pos_type = self.desc[next_coords[1], next_coords[0]]
        if next_pos_type == 'W' or pos_type == 'H' or pos_type == 'G':
            return [(pos, 1.)]
        else:
            return [(next_pos, 1.)]

    @cached_property
    def action_space(self):
        return spaces.Discrete(4, is_distribution=True)

    @cached_property
    def observation_space(self):
        return spaces.Dict({"pos"    : spaces.Discrete(self.n_row * self.n_col),
                            "_reward": spaces.Continuous(0, 1) if self.reward_func == "sparse" else spaces.Continuous(-100, 1),
                            "_done"  : spaces.Bool()})

    def render(self):
        x = self.pos // self.n_col
        y = self.pos % self.n_col

        # paints itself
        for row in range(len(self.desc)):
            for col, val in enumerate(self.desc[row]):
                if x == col and y == row:
                    print("X", end="")
                else:
                    print(" " if val == "F" else val, end="")
            print()

        print()

