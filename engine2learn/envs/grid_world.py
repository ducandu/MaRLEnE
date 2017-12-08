"""
 -------------------------------------------------------------------------
 Engine2Learn - envs/grid_world
 
 A simple grid world test env.
  
 created: 2017/08/31 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from cached_property import cached_property
import numpy as np
from .base import Env
import engine2learn.spaces as spaces
import math
import random


class GridWorld(Env):
    """
    A classic grid world where the action space is up,down,left,right and the
    state space is:
    'S' : starting point
    ' ' : free space
    'W' : wall
    'H' : hole (terminates episode) (to be replaced by W in save-mode)
    'G' : goal state (terminates episode)
    """

    # all available maps
    MAPS = {
        "chain": [
            "G             S             G"
        ],
        "2x2": [
            "SH",
            " G"
        ],
        "4x4": [
            "S   ",
            " H H",
            "   H",
            "H  G"
        ],
        "8x8": [
            "S       ",
            "        ",
            "   H    ",
            "     H  ",
            "   H    ",
            " HH   H ",
            " H  H H ",
            "   H   G"
        ],
        "8x16": [
            "S      H        ",
            "   H       HH   ",
            "    FF   WWWWWWW",
            "  H      W      ",
            "    FF   W  H   ",
            "         W      ",
            "    FF   W      ",
            "  H          H G"
        ],
        "16x16": [
            "S      H        ",
            "           HH   ",
            "    FF   W     W",
            "         W      ",
            "WWW FF      H   ",
            "         W      ",
            " FFFF    W      ",
            "  H          H  ",
            "       H        ",
            "   H       HH   ",
            "WWWW     WWWWWWW",
            "  H      W    W ",
            "    FF   W  H W ",
            "WWWW    WW    W ",
            "    FF   W      ",
            "  H          H G"
        ]
    }

    def __init__(self, desc="4x4", save=False, reward_func="sparse", obs_repr="discr_pos"):
        super().__init__()
        if isinstance(desc, str):
            desc = self.MAPS[desc]
        desc = np.array(list(map(list, desc)))
        desc[desc == 'H'] = ("H" if not save else "W")  # apply safety switch

        self.desc = desc  # desc needs to be indexed as y/x pairs (first row, then column), just as any matrix
        self.n_row, self.n_col = desc.shape
        (start_x,), (start_y,) = np.nonzero(desc == "S")
        self.cam_pix = None

        self.pos0 = self.get_pos(start_x, start_y)
        self.pos = self.pos0

        # a rich reward function gives -1 normally, 1 on end and -100 for falling into a hole
        assert reward_func == "sparse" or reward_func == "rich" or reward_func == "rich_potential"
        self.reward_func = reward_func

        self.obs_repr = obs_repr  # what goes into the obs_dict?

        # store the goal position for proximity calculations
        (self.goal_x,), (self.goal_y,) = np.nonzero(desc == "G")

        # populate our obs_dict
        self.refresh_obs_dict(0, False)

    @property
    def x(self):
        return self.pos // self.n_col

    @property
    def y(self):
        return self.pos % self.n_col

    def get_pos(self, x, y):
        """
        self.pos is counted walking down the rows of the grid first (starting in upper left corner), then along the col-axis

        :param int x: The x coord.
        :param y: The y coord.
        :return: The discrete pos value corresponding to the given x and y.
        :rtype: int
        """
        return x * self.n_col + y

    def refresh_obs_dict(self, reward, done):
        self.obs_dict["_reward"] = reward
        self.obs_dict["_done"] = done

        if self.obs_repr == "discr_pos":
            self.obs_dict["pos"] = self.pos
        elif self.obs_repr == "xy_pos":
            self.obs_dict["x"] = self.x
            self.obs_dict["y"] = self.y
        elif self.obs_repr == "2d_cam":
            self.update_cam_pixels()
            self.obs_dict["cam"] = self.cam_pix

    def reset(self, randomize=False):
        if not randomize:
            self.pos = self.pos0
        else:
            # move to a random first position (empty space, start or fire are all fine)
            while True:
                self.pos = random.choice(range(self.n_row * self.n_col))
                next_state_type = self.desc[self.y, self.x]
                if next_state_type in [" ", "S", "F"]:
                    break

        self.refresh_obs_dict(0, False)
        return self.obs_dict

    def step(self, **kwargs):
        """
        action map:
        0: up
        1: right
        2: down
        3: left

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
        if next_state_type == "H":
            done = True
            reward = -1 if self.reward_func == "sparse" else -100
        elif next_state_type == "F":
            done = False
            reward = -1 if self.reward_func == "sparse" else -10
        elif next_state_type in [" ", "S"]:
            done = False
            reward = 0 if self.reward_func == "sparse" else -1
        elif next_state_type == "G":
            done = True
            reward = 50
        else:
            raise NotImplementedError

        # prepare the obs_dict
        self.pos = next_pos
        self.refresh_obs_dict(reward, done)

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

        increments = np.array([[0, -1], [1, 0], [0, 1], [-1, 0]])
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
        # 4 discrete actions
        return spaces.Discrete(4, is_distribution=True)

    @cached_property
    def observation_space(self):
        # our basic obs_dict (reward and done flag)
        d = {
            "_reward": spaces.Continuous(-1, 1) if self.reward_func == "sparse" else spaces.Continuous(-100, 1),
            "_done": spaces.Bool()
        }
        # add certain keys depending on the desired representation
        if self.obs_repr == "discr_pos":
            d["pos"] = spaces.Discrete(self.n_row * self.n_col)
        elif self.obs_repr == "xy_pos":
            d["x"] = spaces.Continuous(0, self.n_col)
            d["y"] = spaces.Continuous(0, self.n_row)
        else:
            d["cam"] = spaces.Continuous(0, 255, shape=(self.n_row, self.n_col, 3))

        return spaces.Dict(d)

    @property
    def horizon(self):
        return None

    def update_cam_pixels(self):
        # init cam?
        if self.cam_pix is None:
            self.cam_pix = np.zeros(shape=(self.n_row, self.n_col, 3), dtype=float)
        self.cam_pix[:, :, :] = 0  # reset everything

        # first channel -> walls (1) and goal (-1)
        # second channel -> dangers (fire 0.5, holes 1)
        # third channel -> pawn position (1)
        for row in range(self.n_row):
            for col in range(self.n_col):
                field = self.desc[row, col]
                if field == "F":
                    self.cam_pix[row, col, 0] = 0.5
                elif field == "H":
                    self.cam_pix[row, col, 0] = 1
                elif field == "W":
                    self.cam_pix[row, col, 1] = 1
                elif field == "G":
                    self.cam_pix[row, col, 1] = -1  # will this work?
        # overwrite pawn pos
        self.cam_pix[self.y, self.x, 2] = 1

    def render(self):
        # paints itself
        for row in range(len(self.desc)):
            for col, val in enumerate(self.desc[row]):
                if self.x == col and self.y == row:
                    print("X", end="")
                else:
                    print(val, end="")
            print()

        print()

    def get_dist_to_goal(self):
        return math.sqrt((self.x - self.goal_x) ** 2 + (self.y - self.goal_y) ** 2)
