# prototype of a distributed A3C algo running on distributed tensorflow + TensorFlowOnSpark

from tensorflowonspark import TFNode, TFCluster
from pyspark.context import SparkContext
from pyspark.conf import SparkConf
from engine2learn.a3c_net import A3CPolicyNetwork
import numpy as np
from engine2learn.misc.helper import discount


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
def main_fun(argv, ctx):
    import tensorflow as tf
    from tensorflowonspark import TFNode
    from time import sleep
    from engine2learn.envs.grid_world import GridWorld
    # from engine2learn.models.fully_connected_nn import FullyConnectedNN

    # sleep a little for ps jobs to not block the GPUs
    if ctx.job_name == "ps":
        sleep((ctx.worker_num + 1) * 5)

    # model and training parameters
    hidden_units = 128
    gamma = 0.99  # discount factor
    max_episode_len = argv.max_episode_len  # TODO: add others from A3C algo

    # OLD: Tensorflow:
    #ps_hosts = FLAGS.ps_hosts.split(",")
    #worker_hosts = FLAGS.worker_hosts.split(",")
    # create a cluster from the parameter server and worker hosts.
    #cluster = tf.train.ClusterSpec({"ps": ps_hosts, "worker": worker_hosts})
    # create and start a server for the local task
    #server = tf.train.Server(server_or_cluster_def=cluster, job_name=FLAGS.job_name, task_index=FLAGS.task_idx)

    # NEW: TensorFlowOnSpark
    # TODO: get num_gpus and rdma via argv
    cluster_spec, server = TFNode.start_cluster_server(ctx, num_gpus=0, rdma=argv.rdma)

    # if we are a parameter server -> do nothing (we just host the weights of the model)
    if ctx.job_name == "ps":
        server.join()
        return

    # from here on: we are a worker task

    # create our env: This would be a 20tab ue4 Env in the future.
    grid_world = GridWorld("8x8")

    # build graph for asynchronous between-graph replication:
    # - separate client for each task
    # - each client builds same graph
    # - graph puts variables into ps and computationally heavy ops into workers
    with tf.device(tf.train.replica_device_setter(worker_device="/job:worker/task:{}".format(ctx.task_index), cluster=cluster)):

        # build our policy network for doing A3C (outputs=num actions + 1 (value function output))
        policy_network = A3CPolicyNetwork("policy_network", grid_world.observation_space.flat_dim, hidden_units, (grid_world.action_dim + 1))

        global_step = tf.Variable(0)
        train_op = tf.train.AdagradOptimizer(learning_rate=0.01).minimize(policy_network.get_output("loss"), global_step=global_step)

        saver = tf.train.Saver()
        summary_op = tf.summary.merge_all()
        init_op = tf.global_variables_initializer()
    # model has been built in a distributed fashion placing Variables on the ps job and computationally heavy Operations on the worker job

    # add custom summary_writer for the chief worker
    summary_writer = tf.summary.FileWriter(logdir="tensorboard_{}".format(ctx.worker_num), graph=tf.get_default_graph())

    #run session with: config = tf.ConfigProto(log_device_placement=True)
    # create a supervisor for the training process (when to stop, etc..)
    supervisor = tf.train.Supervisor(is_chief=(ctx.task_index == 0),
                                     logdir="/tmp/train_logs",
                                     init_op=init_op,
                                     summary_op=summary_op,
                                     summary_writer=summary_writer,
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
                                         feed_dict={policy_network.get_feed("s"): [grid_world.observation_space["pos"].flatten(observation_dict["pos"])]})
                # [0] b/c we only fed in a single input (#samples=1)
                policy = policy[0]
                value = value[0]
                # pick an action according to the policy output
                a = np.random.choice(policy, p=policy)
                a = np.argmax(policy == a)

                # receive reward rt and new state st'
                observation_dict = grid_world.step(a)  # type: dict

                s_ = observation_dict["pos"]
                r = observation_dict["_reward"]
                is_terminal = observation_dict["_done"]

                t += 1
                episode_observations.append(s_)
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
            advantages = np.asarray(episode_rewards) + np.asarray(gamma * value_list[1:]) - np.asarray(value_list[:-1])
            advantages = discount(advantages, gamma)

            # run asynchronous training
            # the train_ops will update (via minimize(loss)) the weights of our model (which reside in the ps job(s))
            feed_dict = {policy_network.get_feed("R"):          discounted_returns,
                         policy_network.get_feed("s"):          episode_observations,
                         policy_network.get_feed("a"):          episode_actions,
                         policy_network.get_feed("advantages"): advantages}
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

    import argparse
    import sys

    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--tensorboard", help="launch tensorboard process", action="store_true")
    args, rem = parser.parse_known_args()

    # create the spark context object from pyspark
    spark_context = SparkContext(conf=SparkConf().setAppName("A3C test runner"))

    # specify the cluster specs
    num_executors = int(spark_context._conf.get("spark.executor.instances"))
    num_ps = 1
    tensorboard = True

    cluster = TFCluster.run(spark_context, main_fun, sys.argv, num_executors, num_ps, tensorboard, TFCluster.InputMode.TENSORFLOW)
    cluster.shutdown()
