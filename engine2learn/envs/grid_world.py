"""
 -------------------------------------------------------------------------
 AIOpening - 
 grid_world
 
 !!TODO: add file description here!! 
  
 created: 2017/08/31 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

import numpy as np
from engine2learn.envs.base import Env
import engine2learn.spaces as spaces


class GridWorld(Env):
    """
    A classic grid world where the actioni space is up,down,left,right and the
    state space is:
    'S' : starting point
    'F' or '.': free space
    'W' or 'x': wall
    'H' or 'o': hole (terminates episode)
    'G' : goal
    """

    # all available maps
    MAPS = {
        "chain": [
            "GFFFFFFFFFFFFFSFFFFFFFFFFFFFG"
        ],
        "2x2": [
            "SH",
            "FG"
        ],
        "4x4": [
            "SFFF",
            "FHFH",
            "FFFH",
            "HFFG"
        ],
        "8x8": [
            "SFFFFFFF",
            "FFFFFFFF",
            "FFFHFFFF",
            "FFFFFHFF",
            "FFFHFFFF",
            "FHHFFFHF",
            "FHFFHFHF",
            "FFFHFFFG"
        ],
    }

    def __init__(self, desc="4x4", save=False):
        if isinstance(desc, str):
            desc = self.MAPS[desc]
        desc = np.array(list(map(list, desc)))
        desc[desc == '.'] = "F"
        desc[desc == 'o'] = "H"
        desc[desc == 'x'] = "W"
        desc[desc == 'H'] = ("H" if not save else "W")  # apply safety switch

        self.desc = desc
        self.n_row, self.n_col = desc.shape
        (start_x,), (start_y,) = np.nonzero(desc == "S")

        self.pos0 = start_x * self.n_col + start_y
        self.pos = self.pos0
        self.obs_dict = {"pos": self.pos0, "_reward": 0, "_done": False}

        self.domain_fig = None

    def reset(self):
        self.pos = self.pos0
        self.obs_dict["pos"] = self.pos
        self.obs_dict["_reward"] = 0
        self.obs_dict["_done"] = False
        return self.obs_dict

    def set(self, *setter_instructions):
        # simply set our position to some new value
        for instr in setter_instructions:
            assert isinstance(instr, int) and 0 <= instr < self.observation_space["pos"].flat_dim
            self.pos = instr
        self.obs_dict["pos"] = self.pos
        return self.obs_dict

    def current_observation(self):
        return self.obs_dict

    def step(self, action):
        """
        action map:
        0: left
        1: down
        2: right
        3: up
        :param action: should be a one-hot vector encoding the action
        :return: tuple with s', r', is_done, info
        :rtype: tuple
        """
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
            reward = 0
        elif next_state_type in ['F', 'S']:
            done = False
            reward = 0
        elif next_state_type == 'G':
            done = True
            reward = 1
        else:
            raise NotImplementedError

        # set s'=s
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

    @property
    def action_space(self):
        return spaces.Discrete(4)

    @property
    def observation_space(self):
        return spaces.Dict({"pos": spaces.Discrete(self.n_row * self.n_col), "_reward": spaces.Box(-1, 1), "_done": spaces.Discrete(2)})

    @property
    def horizon(self):
        return None

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
