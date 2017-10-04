"""
 -------------------------------------------------------------------------
 engine2learn - factory.py
 
 Factory methods to create the different engine2learn objects.
  
 created: 2017/10/04 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from .envs import Env, UE4Env


def connect_env(type_="ue4", hostname="localhost", port=2017):
    """
    Tries to connect to a running UE4 (maybe headless) instance.
    For now, only ue4 as type is accepted. We will later add other engines to this lib.
    Returns an Env object that can be used to manipulate the environment.

    :param str type_: The engine type. For now, only 'ue4' is supported.
    :param hostname: The hostname on which the engine is listening.
    :param port: The port to connect to.
    :return: The Environment object for further manipulation.
    :rtype: Env
    """

    # for now: the only supported type is ue4
    if type_ == "ue4":
        return UE4Env(hostname, port)  # what other params are necessary?

    raise TypeError("type_ has to be 'ue4'!")

