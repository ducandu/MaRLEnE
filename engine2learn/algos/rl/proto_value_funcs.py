"""
 -------------------------------------------------------------------------
 engine2learn - algos/rl/proto_value_funcs.py
 
 Functions to obtain proto-value functions from MDPs

 [1] A Laplacian Framework for Option Discovery in
 Reinforcement Learning - Machado, Bellemare, Bowling (2017)
 [2] Proto-Value Functions: Developmental Reinforcement Learning -
 Mahadevan (2005)

 created: 2017/10/24 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from engine2learn.envs import Env
from engine2learn.spaces import Dict
import numpy as np


def get_pvfs(env, state_components=None, num_transitions=None, num_rows=None):
    """
    A function to retrieve proto-value functions [2] for an Env (MDP) using the approach in [1]
    TODO: answer question on whether to normalize the env beforehand.

    :param Env env: The Env object to explore and to create PVFs for.
    :param list state_components: A list of components from the observation dictionaries.
    :param int num_transitions: The number of state transitions to do (by random walk)
    :param int num_rows: The number of transitions to include in the final incidence matrix.
    :return: A list of tuples, where 0=eigenvalue of its corresponding eigenvector (1) (list is sorted by eigenvalue (lowest first))
    :rtype: List[Tuple[float,float]]
    """
    state_dim = 0
    assert isinstance(env.observation_space, Dict)
    for comp in state_components:
        state_dim += env.observation_space[comp].flat_dim
    if num_transitions is None:
        num_transitions = state_dim * 10000
    if num_rows is None:
        num_rows = int(num_transitions / 10)

    # init our incidence matrix, into which we will insert our samples
    __T = np.matrix(np.zeros(shape=(num_rows, state_dim)))
    unique_transitions = set()  # to make sure we only store unique transitions

    # reset the env
    obs_dict = env.reset()
    # sample the state space to build the incidence matrix T
    s = None  # state (as feature vector)
    s_ = None  # next state (as feature vector)

    rows_added = 0
    transitions = 0
    while True:
        # extract the actual state components (w/o reward etc..) from the obs_dict and take the difference between the current obs and the last one
        s_ = env.observation_space.flatten(obs_dict, keys=state_components)
        if s is not None:
            delta_s = np.subtract(s_, s)
            lookup_tuple = tuple(delta_s)
            if lookup_tuple not in unique_transitions:
                unique_transitions.add(lookup_tuple)
                # add this transition as a new row to the matrix
                __T[rows_added] = delta_s
                rows_added += 1
                print(".", end="", flush=True)
                # we reached the number of rows in the matrix that we wanted -> stop here
                if rows_added == num_rows:
                    break
        if transitions >= num_transitions:
            break
        # do one transition
        obs_dict = env.step(action=env.action_space.sample())  # random walk
        transitions += 1

        # reset the env or keep playing?
        if obs_dict["_done"] is True:
            obs_dict = env.reset()
            s = None
        else:
            s = s_

    # TODO: sample num_rows from the matrix into a new matrix before doing SVD
    # now calculate the SVD (singular value decomposition) of T to get the right eigen-vectors (which are the needed PVFs)
    _, diag_values, _V_transpose = np.linalg.svd(__T, compute_uv=True)
    # the columns of V are the eigen-vectors of T^T * T, so we need to take the rows here (as we have V^T)
    # - create a map that maps each eigenvalue to it's eigenvector and return that map
    ret = []
    for row, dv in enumerate(diag_values):
        # get eigenvalues by squaring the values (dv) in the (diagonal) SIGMA matrix returned by the SVD procedure
        ret.append((dv**2, _V_transpose[row]))

    return sorted(ret, key=lambda el: el[0])  # sort the list by the first value in each tuple (the eigenvalue)


if __name__ == "__main__":
    from engine2learn.envs import GridWorld
    import matplotlib.pyplot as plt
    from matplotlib import cm
    from mpl_toolkits.mplot3d import Axes3D

    world = GridWorld("8x8", save=True, obs_repr="discr_pos")

    pvfs = get_pvfs(world, num_rows=149, state_components=["pos"])

    # get the pvf we would like to plot (with the nth smallest eigenvalue)
    pvf = np.array(pvfs[0][1]).squeeze()  # 1=the pvf representation (0=eigenvalue)

    # plot the nth PVF
    # create the x,y meshgrid
    x = np.arange(8)
    y = np.arange(8)
    xv, yv = np.meshgrid(x, y)

    # walk through the entire meshgrid and get the pvf value for the x/y position (translate it to a one-hot pos-vector first)
    z = np.zeros(shape=xv.shape)
    for x_ in x:
        for y_ in y:
            pos = world.get_pos(x_, y_)
            pos_repr = world.observation_space["pos"].flatten(pos)
            z[x_, y_] = np.dot(pos_repr, pvf)

    # Plot the surface.
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    surf = ax.plot_surface(xv, yv, z, cmap=cm.coolwarm, linewidth=0, antialiased=False)

    # Customize the z axis.
    ax.set_zlim(-.3, .3)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Proto-Value Function #0")
    #ax.zaxis.set_major_locator(LinearLocator(10))
    #ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

    # Add a color bar which maps values to colors.
    fig.colorbar(surf, shrink=0.5, aspect=5)

    plt.show()
