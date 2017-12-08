b"""
 -------------------------------------------------------------------------
 engine2learn - examples/test_ue4_connection.py
 
 Test a UE4Env connection to some UE4 game listening on a tcp port.
  
 created: 2017/11/05 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from engine2learn import connect_env
import time
import random
from PIL import Image
import numpy as np


capture = False

if __name__ == "__main__":
    print("Starting ...")
    env = connect_env("ue4", port=6025)
    print("Env ({}) created and connected".format(env))

    random.seed(200)
    env.seed(200)

    time_start = time.time()
    # reset the env
    obs_dict = env.reset()
    # write the first observed image
    if capture:
        img = Image.fromarray(obs_dict["Observer:camera"], "RGB")
        img.save("captures/reset.png")  # save first received image as a sanity-check

    # env.set(setters=("Ledge_test:RenderComponent:bSimulatePhysics", True))
    # print("After reset()")

    num_ticks_per_action = 4  # 3600 should cover 1 min in the real game (with 1/60 delta time per tick)
    delta_time = 1 / 60

    for i in range(1000):
        obs_dict = env.step(delta_time=delta_time, num_ticks=num_ticks_per_action,
                            axes=("MoveRight", np.random.choice([-1.0, 1.0, 0.0], p=[0.4, 0.4, 0.2])),
                            actions=("Shoot", random.choice([False, True])))  # False if i % 10 else True
        time_now = time.time()
        ticks = (i + 1) * num_ticks_per_action
        would_be_play_time = ticks * delta_time
        real_time = (time_now - time_start)
        print("ticks={} would-be-play-time={:.2f}sec real-time={:.2f}sec".format(ticks, would_be_play_time, real_time))
        if capture:
            img = Image.fromarray(obs_dict["Observer:camera"], "RGB")
            img.save("captures/{:04d}.png".format(i))  # save all images to disk
    time_end = time.time()

    print("Whole thing took {} seconds.".format(time_end - time_start))

