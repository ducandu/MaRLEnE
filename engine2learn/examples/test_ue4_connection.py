"""
 -------------------------------------------------------------------------
 engine2learn - examples/test_ue4_connection.py
 
 Test a UE4Env connection to some UE4 game listening on a tcp port.
  
 created: 2017/11/05 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from engine2learn.envs.ue4_env import UE4Env
import time
import random


if __name__ == "__main__":
    print("Starting ...")
    env = UE4Env(6025)  # port to connect to
    print("After Env creation")

    env.connect()
    print("After connect()")

    # do some RL :)
    time_start = time.time()
    obs_dict = env.reset()
    env.set(setters=("Ledge_test:RenderComponent:bSimulatePhysics", True))
    print("After reset()")
    for i in range(600):
        obs_dict = env.step(delta_time=1/30, axes=("MoveRight", random.choice([-1.0, 1.0, 0.0])), actions=("Jump", random.choice([False, False, False, False, True])))
        print("step {}".format(i))
    time_end = time.time()

    print("Whole thing took {} seconds.".format(time_end - time_start))

