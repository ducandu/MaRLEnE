"""
 -------------------------------------------------------------------------
 engine2learn - algos/base.py

 Base class for AI algorithms.

 created: 2017/10/11 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""


class Algorithm(object):
    """
    An Algorithm object represents a simple code unit that can be executed in atomic steps within a single thread/process given some input.
    The input can be the result of a former atomic step by the same algorithm and intermediary outputs may be stored for efficiency reasons
    within the Algorithm.
    An Algorithm usually does not own the Model objects that it works on. These are rather handled by the Experiment objects. The reason
    for this separation is that one algo could train some model and then another algo could use that trained model for something else. Both
    these algos would live in an Experiment (which owns the Model objects as well).
    """
    def __init__(self, name):
        self.name = name

    def run_atomic(self, *args):
        """
        Describes a single and unsplittable (atomic) step of the algorithm, e.g. a single run through the main loop of an RL-algo, in which the agent
        takes a single step in the environment and then the algo does something to update its models, tables, etc..
        """
        raise NotImplementedError
