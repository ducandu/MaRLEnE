"""
 -------------------------------------------------------------------------
 MaRLEnE - Machine- and Reinforcement Learning ExtensioN for (game) Engines
 Plugins/MaRLEnE/Scripts/marlene_server.py

 The server running inside UE4 (UnrealEnginePython) and listening on a
 port for incoming ML connections.
 Handles incoming commands from the ML environment such as stepping
 through the game, setting properties, resetting the game, etc..

 created: 2017/10/26 in PyCharm
 (c) 2017-2018 Roberto DeLoris (20tab) & Sven Mika (ducandu)
 -------------------------------------------------------------------------
"""

import asyncio

# cleanup previous tasks
for task in asyncio.Task.all_tasks():
    task.cancel()
