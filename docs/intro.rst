Introduction to engine2learn
============================

.. .. include:: blizzard_copyright_disclaimer.rst

What is engine2learn?
---------------------

Engine2Learn consists of two components:

#. An UnrealEngine 4 (UE4) plugin (C++), allowing game developers to connect their game to a state-of-the-art machine learning (ML) environment
   in order to create better game AIs and smarter NPCs.
#. A python3 machine learning (ML) library with a focus on reinforcement learning (RL) and deep learning (DL) methods.
   Engine2Learn also features an automatic deploy/build/cooking-procedure for running games headlessly on Linux clusters and/or virtual machines (e.g. Vagrant).
   This way, games can be run in parallel on hundreds or thousands of nodes to accelerate learning and to maximize exploration speed for RL-algorithms.
#. Both engine2learn components (UE4 plugin and python lib) connect and talk to each other via TCP sockets and a simple msgpack-based protocol.
   Information flows from the game to the ML-environment in the form of "observations" (e.g. camera rendering results, positions of actors, etc..)
   and from the ML-environment to the game in the form of action instructions (e.g. "moveRight", "Fire", "Jump", etc..).

Main Features
-------------

Simple, yet Powerful
++++++++++++++++++++

Engine2Learn is very lightweight. It comes as a pip-installable python module (``pip install engine2learn``) on the client machine-learning side
as well as a UE4 plugin for the game environment side.


.. .. image:: images/intro_001_level_tmx_file.png
    :alt: a level-tmx file opened in the Tiled editor
    :scale: 75%



