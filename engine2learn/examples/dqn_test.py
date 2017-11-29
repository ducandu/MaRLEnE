# prototype of a deep-q-network algo running on distributed tensorflow + TensorFlowOnSpark

import numpy as np
from pyspark.conf import SparkConf
from pyspark.context import SparkContext
from tensorflowonspark import TFCluster


# main function to be executed by each executor
# Argv contains the full commands line args given on the pyspark command line.
# Ctx contains node metadata like job name and task idx
def main_fun(args, ctx):
    import tensorflow as tf
    from tensorflowonspark import TFNode
    from time import sleep
    import os

    from engine2learn.envs import normalize
    from engine2learn.envs.ue4_env import UE4Env
    from engine2learn.misc.helper import discount
    from engine2learn.examples.models.dqn_net import DQNPolicyNetwork

    is_chief = False

    # sleep a little for ps jobs to not block the GPUs
    if ctx.job_name == "ps":
        sleep((ctx.worker_num + 1) * 5)
    # 1st (non-ps) worker -> check for debug option
    elif ctx.task_index == 0:  # 1st worker
        is_chief = True
        if args.debug_worker:
            # set a softlink to ${SPARK_HOME}/work/pycharm_debug/ from the current pwd
            os.system("rm -rf ${SPARK_HOME}/work/pycharm_debug")  # delete old softlink
            os.system("ln -s "+os.getcwd()+" ${SPARK_HOME}/work/pycharm_debug")  # create new one

            import pydevd
            pydevd.settrace("localhost", port=20023, stdoutToServer=True, stderrToServer=True)  # DEBUG
        print("IN MAIN_FUN: job_name={} worker_num={} tas_idx={}".format(ctx.job_name, ctx.worker_num, ctx.task_index))

    # model and training parameters
    hidden_units = args.hidden_units
    gamma = args.gamma  # discount factor
    max_episode_len = args.max_episode_len
    num_episodes = args.num_episodes
    learning_rate = args.learning_rate
    beta = args.beta

    # create a cluster consisting of 1 parameter server and n worker hosts
    # create and start a server for the local task
    cluster_spec, server = TFNode.start_cluster_server(ctx, num_gpus=0, rdma=args.rdma)

    # if we are a parameter server -> do nothing (we just host the weights of the model)
    if ctx.job_name == "ps":
        server.join()
        return

    # from here on: we are a worker task

    # create our env: This is a 20tab UE4Env
    # remember to always normalize
    env = normalize(UE4Env(port=6025), keys_to_globally_normalize=["Observer:camera"])

    # build graph for asynchronous between-graph replication:
    # - separate client for each task
    # - each client builds same graph
    # - graph puts variables into ps and computationally heavy ops into workers
    with tf.device(tf.train.replica_device_setter(worker_device="/job:worker/task:{}".format(ctx.task_index), cluster=cluster_spec)):

        # DEBUG!
        #tf.set_random_seed(9999)

        # build our policy network for doing A3C (outputs=num actions + 1 (value function output))
        cam_shape = env.observation_space["Observer:camera"].shape
        policy_network = DQNNetwork("policy_network", cam_shape[0], cam_shape[1], hidden_units, num_action_mappings=1, num_axis_mappings=2, beta=beta)

        global_step = tf.Variable(0)
        train_op = tf.train.AdagradOptimizer(learning_rate=learning_rate).minimize(policy_network.get_output("loss"), global_step=global_step)
        saver = tf.train.Saver()
        init_op = tf.global_variables_initializer()

    # model has been built in a distributed fashion placing Variables on the ps job and computationally heavy Operations on the worker job

    # add custom summary_writer for the chief worker
    summary_writer = None
    if is_chief:
        summary_writer = tf.summary.FileWriter(logdir="/vagrant/_vagrant_box_tmp/tensorboard_{}".format(ctx.worker_num), graph=tf.get_default_graph())

    # run session with: config = tf.ConfigProto(log_device_placement=True)
    # create a supervisor for the training process (when to stop, etc..)
    supervisor = tf.train.Supervisor(is_chief=is_chief,
                                     logdir="/vagrant/_vagrant_box_tmp/train_logs",
                                     init_op=init_op,
                                     summary_op=None,  # we have several summary ops
                                     summary_writer=summary_writer,
                                     save_summaries_secs=30 if is_chief else 0,
                                     saver=saver,
                                     global_step=global_step,
                                     save_model_secs=300)

    # the supervisor now manages the session:
    # takes care of initialization or loading from disk
    # closing when done or an error occurs
    with supervisor.managed_session(server.target) as sess:
        episode = 0
        goals_reached = 0  # how many times altogether have we reached the goal state?
        while not supervisor.should_stop() and episode < num_episodes:
            # do a single rollout through our env
            episode += 1

            # reset either way, even if the episode was not done from before
            #observation_dict = grid_world.current_observation
            #if observation_dict["_done"]:
            if args.render:
                env.render()
            observation_dict = env.reset()
            print("STARTING EPISODE {} (reset env):".format(episode))
            print("after reset: _done={} _reward={} pos={} ({},{}) orient={}".format(observation_dict["_done"], observation_dict["_reward"], env._wrapped_env.pos,
                                                                                     env._wrapped_env.x, env._wrapped_env.y, observation_dict["orientation"]))

            # generate one rollout
            episode_cam_observations = []  # list of camera outputs that we will encounter in this episode (except for very first one)
            episode_other_observations = []  # list of other observations that we will encounter in this episode (except for very first one)
            episode_action_mappings = []  # list of action mappings that we will take in this episode
            episode_axis_mappings = []  # list of axis mappings that we will take in this episode
            episode_rewards = []  # list of rewards that we will encounter in this episode
            episode_values = []  # list of value outputs that we will encounter in this episode
            episode_pos = [grid_world._wrapped_env.pos]  # list of all positions visited in the episode
            episode_orig_return = 0.0  # non-normalized/non-discounted return for this episode
            cam = observation_dict["camera"]
            health_orient = np.array([observation_dict["health"], observation_dict["orientation"]])
            t = 0
            r_orig = 0
            is_terminal = False
            while observation_dict["_done"] is False and t < max_episode_len:
                # perform action (at) according to policy π(at|st;θ')
                forward_out, turn_out, jump_out, value = sess.run(
                    policy_network.get_output(["forward_move_out", "turn_out", "jump_out", "value"]),
                    feed_dict={policy_network.get_feed("cam"): [cam], policy_network.get_feed("health_orient"): [health_orient]}
                )
                # [0] b/c we only fed in a single input (#samples=1) (forward_out, turn_out and jump_out are already single scalars)
                value = value[0]

                # discretize our axis mappings to -1, 0 or 1
                forward_out_discr = -1 if forward_out <= -0.5 else 1 if forward_out >= 0.5 else 0
                turn_out_discr = -1 if turn_out <= -0.5 else 1 if turn_out >= 0.5 else 0

                # pick forward movement/turn/jump actions according to the distribution(s) (continuous) outputs
                # forward_move =
                # a = np.random.choice(policy, p=policy)
                # a = np.argmax(policy == a)

                # do one step
                print("moveForward={} turn={} jump={}".format(forward_out_discr, turn_out_discr, bool(jump_out)))
                observation_dict = grid_world.step(mappings={"moveForward": forward_out_discr, "turn": turn_out_discr, "jump": bool(jump_out)})  # type: dict
                if args.render:
                    grid_world.render()
                print("value={}".format(value))

                cam = observation_dict["camera"]
                health_orient = np.array([observation_dict["health"], observation_dict["orientation"]])
                r = observation_dict["_reward"]
                r_orig = grid_world.current_obs_original["_reward"]
                print("r_orig={}".format(r_orig))
                is_terminal = observation_dict["_done"]

                t += 1
                episode_cam_observations.append(cam)
                episode_other_observations.append(health_orient)
                episode_action_mappings.append([jump_out])
                episode_axis_mappings.append([forward_out, turn_out])
                episode_rewards.append(r)
                episode_values.append(value)
                episode_orig_return += r_orig
                episode_pos.append(grid_world._wrapped_env.pos)
                # T ← T + 1  # see return values

            if is_terminal:
                _R = 0
                # did we reach the goal
                if r_orig >= 1:
                    goals_reached += 1
            else:
                # bootstrap from last observed state
                _R = sess.run(policy_network.get_output("value"),
                              feed_dict={policy_network.get_feed("cam"): [cam],
                                         policy_network.get_feed("health_orient"): [health_orient]
                                         }
                              )
                _R = _R[0]
                # supervisor.summary_computed(sess, summary)

            distance_to_goal = grid_world._wrapped_env.get_dist_to_goal()
            pix_render = grid_world._wrapped_env.render_pygame(pos_list=episode_pos)

            # the list of all rewards observed plus the bootstrapped value estimate for the last state
            reward_list_and_value_at_end = episode_rewards + [_R]
            # accumulated and discounted returns (without the terminal-state return)
            discounted_returns = discount(reward_list_and_value_at_end, gamma)[:-1]
            # all observed value predictions
            value_list = episode_values + [_R]
            print("EPISODE {} ended: reward_list_and_value_at_end={} value_list={}".format(episode, reward_list_and_value_at_end, value_list))

            # use "Generalized Advantage Estimation" [2] (different from original A3C paper)
            # GAE(γ, 0) : At = δt = rt + γV (st+1) − V (st)
            advantages = np.asarray(episode_rewards) + np.asarray(value_list[1:]) * gamma - np.asarray(value_list[:-1])
            advantages = discount(advantages, gamma)
            print("\tadvantages={}".format(advantages))

            # run asynchronous training
            # the train_ops will update (via minimize(loss)) the weights of our model (which reside in the ps job(s))
            feed_dict = {policy_network.get_feed("episode_orig_return"):  episode_orig_return,
                         policy_network.get_feed("len_episode"):     t,
                         policy_network.get_feed("goals_reached"):   goals_reached,
                         policy_network.get_feed("distance_to_goal"): distance_to_goal,
                         policy_network.get_feed("R"):               discounted_returns,
                         policy_network.get_feed("cam"):             episode_cam_observations,
                         policy_network.get_feed("health_orient"):   episode_other_observations,
                         policy_network.get_feed("action_mappings"): episode_action_mappings,
                         policy_network.get_feed("axis_mappings"):   episode_axis_mappings,
                         policy_network.get_feed("advantage"):       advantages}
            if is_chief:
                value_loss, policy_loss, entropy, loss, summary_get_action, summary_train, _, gs =\
                    sess.run(policy_network.get_output(["value_loss", "policy_loss", "entropy", "loss", "summary_get_action", "summary_train"])+
                             [train_op, global_step], feed_dict=feed_dict)
                supervisor.summary_computed(sess, summary_get_action, global_step=gs)
                supervisor.summary_computed(sess, summary_train, global_step=gs)
            else:
                value_loss, policy_loss, entropy, loss, _, _ =\
                    sess.run(policy_network.get_output(["value_loss", "policy_loss", "entropy", "loss"]) + [train_op, global_step],
                             feed_dict=feed_dict)

    supervisor.stop()


if __name__ == "__main__":
    #tf.app.run()
    import argparse

    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--tensorboard", help="launch tensorboard process", action="store_true")
    parser.add_argument("--max_episode_len", help="The max. number of steps to take in one episode", type=int, default=50)
    parser.add_argument("--num_episodes", help="The max. number of episodes to explore (per worker)", type=int, default=1000)
    parser.add_argument("--hidden_units", help="The number of hidden units in the final policy fc layer", type=int, default=128)
    parser.add_argument("--render", help="Render the world one frame before resetting", action="store_true")
    parser.add_argument("--rdma", help="", action="store_true")
    parser.add_argument("--gamma", help="The discount factor gamma", type=float, default=0.99)
    parser.add_argument("--debug_worker", help="Debug the first spark worker process (job=worker, task-idx=0)", action="store_true")
    parser.add_argument("--learning_rate", help="The learning rate of the optimizer", type=float, default=0.0001)
    parser.add_argument("--beta", help="The weight for entropy within the loss term", type=float, default=0.0001)
    parser.add_argument("--num_workers", help="The number of workers to use (including the parameters server)", type=int, default=3)

    # only parse what we have added above, the rest of the given arguments, return in rem
    args, rem = parser.parse_known_args()

    # create the spark context object from pyspark
    # TODO: fix this environment variable mess
    conf = SparkConf().setMaster("local[3]").setAppName("DQN_test").conf.setSparkHome("/home/ubuntu/spark-2.2.0-bin-hadoop2.7")
    sc = SparkContext(conf=conf)

    # specify the cluster specs
    num_executors = conf.get("spark.executor.instances", 5)
    num_ps = 1

    # question: run samplers already here?

    cluster = TFCluster.run(sc, main_fun, args, num_executors, num_ps, args.tensorboard, TFCluster.InputMode.TENSORFLOW)
    cluster.shutdown()
