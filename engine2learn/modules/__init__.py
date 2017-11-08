"""
 -------------------------------------------------------------------------
 AIOpening - modules/__init__.py

 Neural Net Modules constructed with deepmind/sonnet

 created: 2017/08/31 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from .fully_connected_module import FullyConnectedModule
from .convolutional_2d_module import Convolutional2DModule
from .splitter import SplitterModule
from .flatten_layer import FlattenLayer


__all__ = ["FullyConnectedModule", "Convolutional2DModule", "FlattenLayer", "SplitterModule"]

