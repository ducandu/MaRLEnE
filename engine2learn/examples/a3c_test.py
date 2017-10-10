# prototype of a distributed A3C algo running on distributed tensorflow + TensorFlowOnSpark

from tensorflowonspark import TFCluster
from pyspark.context import SparkContext
from pyspark.conf import SparkConf
import numpy as np


# flags for defining the tf.train.ClusterSpec
#tf.app.flags.DEFINE_string("ps_hosts", "", "comma-separated list of parameter server hostname:port pairs")
#tf.app.flags.DEFINE_string("worker_hosts", "", "comma-separated list of worker hostname:port pairs")
#tf.app.flags.DEFINE_string("demo_host", "", "single 'demo' hostname:port specification")

# flags for defining the tf.train.Server
#tf.app.flags.DEFINE_string("job_name", "", "One of 'ps', 'demo' or 'worker'")
#tf.app.flags.DEFINE_integer("task_idx", 0, "Index of the task within its job")

#FLAGS = tf.app.flags.FLAGS


# Main function to be executed by each worker process.
# Argv contains the full commands line args given on the pyspark command line.
# Ctx contains node metadata like job name and task idx
def main_fun(args, ctx):
    import tensorflow as tf
    from tensorflowonspark import TFNode
    from time import sleep

    from engine2learn.envs import normalize
    from engine2learn.envs.grid_world import GridWorld
    from engine2learn.misc.helper import discount
    from engine2learn.a3c_net import A3CPolicyNetwork

    is_chief = False

    # sleep a little for ps jobs to not block the GPUs
    if ctx.job_name == "ps":
        sleep((ctx.worker_num + 1) * 5)
    # 1st (non-ps) worker -> check for debug option
    elif ctx.task_index == 0:  # 1st worker
        is_chief = True
        if args.debug_worker:
            import pydevd
            pydevd.settrace("localhost", port=20023, stdoutToServer=True, stderrToServer=True)  # DEBUG
        print("IN MAIN_FUN: job_name={} worker_num={} tas_idx={}".format(ctx.job_name, ctx.worker_num, ctx.task_index))

    # model and training parameters
    hidden_units = 128
    gamma = 0.9  # discount factor
    max_episode_len = args.max_episode_len

    # create a cluster consisting of 1 parameter server and n worker hosts
    # create and start a server for the local task
    cluster_spec, server = TFNode.start_cluster_server(ctx, num_gpus=0, rdma=args.rdma)

    # if we are a parameter server -> do nothing (we just host the weights of the model)
    if ctx.job_name == "ps":
        server.join()
        return

    # from here on: we are a worker task

    # create our env: This would be a 20tab ue4 Env in the future.
    # remember to always normalize
    grid_world = normalize(GridWorld("8x8", save=False, reward_func="rich"))


    # build graph for asynchronous between-graph replication:
    # - separate client for each task
    # - each client builds same graph
    # - graph puts variables into ps and computationally heavy ops into workers
    with tf.device(tf.train.replica_device_setter(worker_device="/job:worker/task:{}".format(ctx.task_index), cluster=cluster_spec)):

        # build our policy network for doing A3C (outputs=num actions + 1 (value function output))
        policy_network = A3CPolicyNetwork("policy_network", grid_world.observation_space["pos"].flat_dim, hidden_units, grid_world.action_dim,
                                          beta=0.001)

        global_step = tf.Variable(0)
        train_op = tf.train.AdagradOptimizer(learning_rate=0.0005).minimize(policy_network.get_output("loss"), global_step=global_step)
        saver = tf.train.Saver()
        # TODO: split up summaries for policy/value output (input=s) as well as for policy-gradient updates (input=s,a,R,advantage)
        #summary_op = tf.summary.merge()
        init_op = tf.global_variables_initializer()

    # model has been built in a distributed fashion placing Variables on the ps job and computationally heavy Operations on the worker job

    # add custom summary_writer for the chief worker
    summary_writer = None
    if is_chief:
        summary_writer = tf.summary.FileWriter(logdir="/vagrant/_vagrant_box_tmp/tensorboard_{}".format(ctx.worker_num), graph=tf.get_default_graph())

    #run session with: config = tf.ConfigProto(log_device_placement=True)
    # create a supervisor for the training process (when to stop, etc..)
    supervisor = tf.train.Supervisor(is_chief=is_chief,
                                     logdir="/vagrant/_vagrant_box_tmp/train_logs",
                                     init_op=init_op,
                                     summary_op=None,  # we have several summary ops
                                     summary_writer=summary_writer,
                                     save_summaries_secs=30 if is_chief else 0,
                                     saver=saver,
                                     global_step=global_step,
                                     save_model_secs=600)

    # the supervisor now manages the session:
    # takes care of initialization or loading from disk
    # closing when done or an error occurs
    with supervisor.managed_session(server.target) as sess:
        step = 0
        while not supervisor.should_stop() and step < 1000:
            # do a single rollout through our env
            observation_dict = grid_world.current_observation()  # type: dict
            # reset if the episode was done from before
            if observation_dict["_done"]:
                observation_dict = grid_world.reset()

            # generate one rollout
            episode_observations = []  # list of states that we will encounter in this episode (except for first state)
            episode_actions = []  # list of actions that we will take in this episode
            episode_rewards = []  # list of rewards that we will encounter in this episode
            episode_values = []  # list of value outputs that we will encounter in this episode
            episode_return = 0.0
            s = observation_dict["pos"]
            t = 0
            is_terminal = False
            while observation_dict["_done"] is False and t < max_episode_len:
                # perform action (at) according to policy π(at|st;θ')
                policy, value = sess.run([policy_network.get_output("policy"),
                                          policy_network.get_output("value")],
                                         feed_dict={policy_network.get_feed("s"): [grid_world.observation_space["pos"].flatten(s)]})
                # [0] b/c we only fed in a single input (#samples=1)
                policy = policy[0]
                value = value[0]
                # pick an action according to the policy output
                a = np.random.choice(policy, p=policy)
                a = np.argmax(policy == a)

                # receive reward rt and new state st'
                observation_dict = grid_world.step(action=a)  # type: dict

                s_ = observation_dict["pos"]
                r = observation_dict["_reward"]
                is_terminal = observation_dict["_done"]

                t += 1
                episode_observations.append(grid_world.observation_space["pos"].flatten(s_))
                episode_actions.append(a)
                episode_rewards.append(r)
                episode_values.append(value)
                episode_return += r

                # T ← T + 1  # see return values
                s = s_

            if is_terminal:
                _R = 0
            else:
                # bootstrap from last observed state
                _R = sess.run(policy_network.get_output("value"),
                              feed_dict={policy_network.get_feed("s"): [grid_world.observation_space["pos"].flatten(s)]})
                _R = _R[0]

            # the list of all rewards observed plus the bootstrapped value estimate for the last state
            reward_list_and_value_at_end = episode_rewards + [_R]
            # accumulated and discounted returns (without the terminal-state return)
            discounted_returns = discount(reward_list_and_value_at_end, gamma)[:-1]
            # all observed value predictions
            value_list = episode_values + [_R]

            # use "Generalized Advantage Estimation" [2] (different from original A3C paper)
            # GAE(γ, 0) : At = δt = rt + γV (st+1) − V (st)
            advantages = np.asarray(episode_rewards) + np.asarray(value_list[1:]) * gamma - np.asarray(value_list[:-1])
            advantages = discount(advantages, gamma)

            # run asynchronous training
            # the train_ops will update (via minimize(loss)) the weights of our model (which reside in the ps job(s))
            feed_dict = {policy_network.get_feed("R"):          discounted_returns,
                         policy_network.get_feed("s"):          episode_observations,
                         policy_network.get_feed("a"):          episode_actions,
                         policy_network.get_feed("advantage"): advantages}
            if is_chief:
                value_loss, policy_loss, entropy, loss, _, summary, gs = sess.run([policy_network.get_output("value_loss"),
                                                                                  policy_network.get_output("policy_loss"),
                                                                                  policy_network.get_output("entropy"),
                                                                                  policy_network.get_output("loss"),
                                                                                  train_op,
                                                                                  policy_network.get_output("summary_pol_grad_opt"),
                                                                                  global_step],
                                                                                 feed_dict=feed_dict)
                supervisor.summary_computed(sess, summary, global_step=gs)
            else:
                value_loss, policy_loss, entropy, loss, _, _ = sess.run([policy_network.get_output("value_loss"),
                                                                                  policy_network.get_output("policy_loss"),
                                                                                  policy_network.get_output("entropy"),
                                                                                  policy_network.get_output("loss"),
                                                                                  train_op,
                                                                                  global_step],
                                                                                 feed_dict=feed_dict)

    supervisor.stop()

if __name__ == "__main__":
    #tf.app.run()
    import os
    import argparse
    import sys

    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--tensorboard", help="launch tensorboard process", action="store_true")
    parser.add_argument("--max_episode_len", type=int, help="The max. number of steps to take in one episode", default=1000)
    parser.add_argument("--rdma", help="", action="store_true")
    parser.add_argument("--debug_worker", help="Debug the first spark worker process (job=worker, task-idx=0)", action="store_true")
    # only parse what we have added above, the rest of the given arguments, return in rem
    args, rem = parser.parse_known_args()

    # create the spark context object from pyspark
    conf = SparkConf().setMaster("spark://ubuntu-xenial:7077").setAppName("A3C_test").\
        setSparkHome("/home/ubuntu/TensorFlowOnSpark/spark-2.2.0-bin-hadoop2.7")  # TODO: fix this environment variable mess
    spark_context = SparkContext(conf=conf)

    # specify the cluster specs
    num_executors = conf.get("spark.executor.instances", 3)
    num_ps = 1

    #sys.argv.extend([1000, True])
    cluster = TFCluster.run(spark_context, main_fun, args, num_executors, num_ps, args.tensorboard, TFCluster.InputMode.TENSORFLOW)
    cluster.shutdown()
