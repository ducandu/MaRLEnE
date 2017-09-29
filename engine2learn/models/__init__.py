"""
 -------------------------------------------------------------------------
 Engine2Learn - models/__init__.py
 
 created: 2017/09/01 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from .base import Model
from .fully_connected_nn import FullyConnectedNN

__all__ = ["Model", "FullyConnectedNN"]

