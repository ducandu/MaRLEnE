"""
 -------------------------------------------------------------------------
 engine2learn - algos/rl/auto_option_discovery.py
 
 An algorithm to automatically detect options in MDPs
  
 created: 2017/10/25 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

import tensorflow as tf
import sonnet as snt
from engine2learn.models import Model
from engine2learn.spaces import Dict
from engine2learn.envs import Env


# first level of abstraction

# init incoming hidden states as an embedding with n rows (num options) and m columns (dimensions of hidden state vectors)
# HORSE - hierarchical option retrieval in simulated environments
class HORSELayer(Model):
    def __init__(self, name, level,
                 env, state_components=None, num_options=None, dim_hidden_states=None, num_lstm_layers=1, pct_abstraction=None, **kwargs):
        """
        :param str name: The name of the model.
        :param int level: The hierarchy level (0=primitive actions; 1=first option layer, etc..).
        :param Env env: The environment object that this model needs to be "fitted" to.
        :param List[str] state_components: The list of state keys (components) used for state-representation from the env's observation_space.
        :param List[int] num_options: The number of options for this hierarchy layer.
        :param dim_hidden_states: The number of hidden-state dimensions.
        :param num_lstm_layers: The number of LSTM layers to stack on top of each other.
        :param pct_abstraction_per_level: The percentage of state-space abstraction applied to the env's state.
        """
        self.env = env
        self.state_components = state_components
        assert isinstance(env.observation_space, Dict)
        self.state_dim = env.observation_space.flatten(env.observation_space.sample(), state_components=state_components)
        self.state_dim_abs = int(self.state_dim * (1 - (pct_abstraction / 100)))
        self.num_options = num_options
        self.dim_hidden_states = dim_hidden_states
        self.num_lstm_layers = num_lstm_layers
        self.pct_abstraction = pct_abstraction

        super().__init__(name, **kwargs)

    def construct(self):
        # define our inputs to this graph
        in_state, in_abs_state = self.add_feeds(
            # for inference
            ([None, self.state_dim], "in_state"),  # the observed state
            ([None, self.state_dim_abs], "in_abs_state"),  # goal
            # for training
            #([None], "in_actions"),  # the actions actually taken
            #([None, self.dim_goal_states], "in_future_states"),  # the future measurements actually observed
        )

        # concat observed state and
        # convolutional module for processing (and flattening) the cam signal

        conv2d = snt_nets.ConvNet2D(output_channels=[4, 8],
                                    kernel_shapes=[(7, 7), (4, 4)],
                                    strides=[(2, 2), (1, 1)],
                                    paddings=[snt.SAME],
                                    activation=tf.nn.relu,
                                    activate_final=True,
                                    name="conv2d_module")
        conv2d_out = conv2d(in_cam)  # push cam through our conv layer
        # flatten our conv2d output
        flat_from_conv = snt.FlattenTrailingDimensions(dim_from=1, name="conv2d_flat")
        flat_from_conv_out = flat_from_conv(conv2d_out)

        tf.summary.histogram("cam", in_cam)
        tf.summary.histogram("conv2d_out", conv2d_out)
        tf.summary.histogram("flat_from_conv_out", flat_from_conv_out)
        tf.summary.histogram("conv2d_weights", conv2d._graph._collections["trainable_variables"][0])
        tf.summary.histogram("conv2d_biases", conv2d._graph._collections["trainable_variables"][1])

        # goal fc module
        in_goal_module = FullyConnectedModule("in_goal_module", self.num_nodes_goal, activations=lrelu)
        in_goal_out = in_goal_module(in_goal)

        # concat with incoming goal state (this is our J from the paper)
        out_j = tf.concat([flat_from_conv_out, in_goal_out], axis=1, name="in_j")

        # fully connected modules for parallel expectation and action streams
        expectation_module = FullyConnectedModule("expectation_module", [self.num_hidden_exp_and_a, self.dim_goal_states], activations=lrelu)
        expectation_out = expectation_module(out_j)
        expectation_tiled = tf.tile(expectation_out, [1, self.num_actions], name="expectation_tiled")
        actions_module = FullyConnectedModule("actions_module", [self.num_hidden_exp_and_a, self.dim_goal_states * self.num_actions], activations=lrelu)
        actions_out = actions_module(out_j)
        actions_out_split = tf.split(actions_out, num_or_size_splits=self.num_actions, axis=1, name="actions_split_by_action")  # a list
        actions_out_stacked = tf.stack(actions_out_split, axis=1, name="actions_stacked_after_split")  # a tensor again (rank 3: batch, action, action-predicted-output)
        actions_out_mean = tf.reduce_mean(actions_out_stacked, axis=1, name="actions_mean")
        actions_out_mean_tiled = tf.tile(actions_out_mean, [1, self.num_actions], name="actions_mean_tiled")
        actions_out_normalized = tf.subtract(actions_out, actions_out_mean_tiled, name="actions_normalized")

        prediction = tf.add(expectation_tiled, actions_out_normalized, "prediction")

        # pick an action from the prediction (given an input goal) by argmax'ing(a) the similarity between incoming goal and predicted state
        # - the following assumes that we only have one sample in our batch
        in_goal_tiled = tf.tile(in_goal, [1, self.num_actions], name="in_goal_tiled")
        # get some delta between the predictions and our wanted goal
        diff_pred_minus_in_goal = tf.subtract(prediction, in_goal_tiled, name="diff_pred_minus_in_goal")
        # split by action
        diff_pred_minus_in_goal_by_action = tf.split(
            diff_pred_minus_in_goal, num_or_size_splits=self.num_actions, axis=1, name="diff_pred_minus_in_goal_by_action")
        # re-stack
        diff_pred_minus_in_goal_by_action_stacked = tf.stack(diff_pred_minus_in_goal_by_action, axis=1, name="diff_pred_minus_in_goal_by_action_stacked")
        diff_pred_minus_in_goal_reduced_by_action = tf.reduce_sum(
            diff_pred_minus_in_goal_by_action_stacked, axis=2, name="diff_pred_minus_in_goal_by_action_sum")
        actions = tf.argmin(diff_pred_minus_in_goal_reduced_by_action, axis=1, name="actions")
        action = actions[0]

        # training operations
        # TODO: add actually taken action as batched feed for training

        loss = tf.reduce_sum(tf.square(tf.subtract(prediction, in_goal)))

        # define our outputs
        #self.add_outputs(# DEBUG
        #                 ("forward_turn_mean", forward_turn_mean), ("forward_turn_var", forward_turn_var), ("jump_prob", jump_prob), ("value", value),
        #                 ("policy_loss", policy_loss), ("value_loss", value_loss),
        #                 ("entropy", entropy), ("loss", loss),
        #                 ("gradients", gradients),
        #                 ("summary_get_action", summary_get_action),
        #                 ("summary_train", summary_train),
        #                 ("forward_move_out", forward_move_out),
        #                 ("turn_out", turn_out),
        #                 ("jump_out", jump_out))


        pass


