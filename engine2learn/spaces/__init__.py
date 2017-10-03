"""
 -------------------------------------------------------------------------
 AIOpening - __init__.py

 Defines the Spaces (action/state space) base class

 created: 2017/09/01 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from .dict import Dict
from .tuple import Tuple
from .discrete import Discrete
from .continuous import Continuous
from .base import Space

__all__ = ["Space", "Discrete", "Continuous", "Tuple", "Dict"]

