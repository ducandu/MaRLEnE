from engine2learn.models.base import Model
from engine2learn.modules import FullyConnectedModule, SplitterModule
# from engine2learn.modules.convolutional_2d_module import Convolutional2DModule
import sonnet.python.modules.nets as snt_nets
import sonnet as snt
# from engine2learn.modules.softmax_and_linear_output import SoftmaxAndLinearOutputModule
from math import pi as PI

import tensorflow as tf


class DQNPolicyNetwork(Model):
    """
    A policy network used by this example:
    Basic fully connected NN with two output "sections", one softmax layer for the action probabilities (policy),
    one single linear output for the state value prediction.
    """
    def __init__(self, name, cam_width, cam_height, num_hidden, num_action_mappings, num_axis_mappings, **kwargs):
        self.cam_width = cam_width
        self.cam_height = cam_height
        self.num_hidden = num_hidden
        self.num_action_mappings = num_action_mappings
        self.num_axis_mappings = num_axis_mappings
        self.learning_rate = kwargs.get("learning_rate", 0.01)
        self.beta = kwargs.get("beta", 0.0001)  # the weight for the entropy regularizer term (10e-4 according to [1])
        self.optimizer = tf.train.RMSPropOptimizer(learning_rate=self.learning_rate)

        super().__init__(name, **kwargs)

    def construct(self):
        # [1] Mnih et al 2015

        # define our inputs to this graph
        cam = self.add_feeds(([None, self.cam_height, self.cam_width, 4], "cam"))  # 4 time steps make up one state description (to be able to capture speed)

        # convolutional module for processing (and flattening) the cam signal
        # - use same params as Mnih et al in their 2015 paper
        conv2d = snt_nets.ConvNet2D(output_channels=[32, 64, 64],
                                    kernel_shapes=[(8, 8), (4, 4), (3, 3)],
                                    strides=[(4, 4), (2, 2), (1, 1)],
                                    paddings=[snt.SAME],
                                    activation=tf.nn.relu,
                                    activate_final=True,
                                    name="conv2d_module")
        conv2d_out = conv2d(cam)  # push cam through our 1st conv layer
        # flatten our conv2d output
        flat_from_conv = snt.FlattenTrailingDimensions(dim_from=1, name="conv2d_flat")
        flat_from_conv_out = flat_from_conv(conv2d_out)
        # DEBUG:
        tf.summary.histogram("cam", cam)
        tf.summary.histogram("conv2d_out", conv2d_out)
        tf.summary.histogram("flat_from_conv_out", flat_from_conv_out)
        tf.summary.histogram("conv2d_weights", conv2d._graph._collections["trainable_variables"][0])
        tf.summary.histogram("conv2d_biases", conv2d._graph._collections["trainable_variables"][1])
        # tf.summary.scalar("len_episode", len_episode)
        # tf.summary.scalar("goals_reached", goals_reached)
        # tf.summary.scalar("distance_to_goal", distance_to_goal)

        # concat with health and orientation
        flat_input = tf.concat([flat_from_conv_out, health_and_orient], axis=1, name="flat_input")
        # DEBUG:
        #tf.summary.histogram("flat_input", flat_input)

        # fully connected module in between flattened in and output softmax (1 layer: input/hidden)
        fc = FullyConnectedModule("fc_module", [self.num_hidden, self.num_action_mappings + 2*self.num_axis_mappings + 1], activations=[tf.nn.relu, None])
        fully_connected_out = fc(flat_input)

        # 2 axis mappings (forward and turn, -1 to 1), each 1 linear (mean) and 1 softplus (variance), 1 action mapping (jump, 0 to 1 sigmoid), 1 value (linear)
        splitter = SplitterModule("splitter_module", splits=[2, 2, 1, 1], axis=1, activations=[tf.tanh, tf.nn.softplus, tf.nn.sigmoid, None])
        forward_turn_mean, forward_turn_var, jump_prob, value = splitter(fully_connected_out)

        # squeeze output through: policy output and value function
        #soft_linear = SoftmaxAndLinearOutputModule("soft_linear", self.num_actions + 1, 1)

        #with tf.name_scope("policy_and_value_output"):
        #    policy, value = soft_linear(fc_out)
        # make value and jump just rank=1 (1 scalar value per batch item)
        value = tf.reshape(value, [-1])
        jump_prob = tf.reshape(jump_prob, [-1])

        # the output normal distribution for all input axis mappings
        pdf = tf.contrib.distributions.MultivariateNormalDiag(loc=forward_turn_mean, scale_diag=forward_turn_var)
        # and the one action mapping (Bernoulli)
        pmf = tf.contrib.distributions.Bernoulli(probs=jump_prob)

        # calculate a sample action for inference and policy-gradient training
        # get a single output sample (action; take the first one ([0]) as we assume that when we query for actions, we only send in len=1 batch)
        sample = pdf.sample()[0]
        forward_move_out = sample[0]
        turn_out = sample[1]
        jump_out = pmf.sample()[0]
        tf.summary.scalar("forward_mean", forward_turn_mean[0][0])
        tf.summary.scalar("turn_mean", forward_turn_mean[0][1])
        tf.summary.scalar("forward_variance", forward_turn_var[0][0])
        tf.summary.scalar("turn_variance", forward_turn_var[0][1])
        tf.summary.scalar("jump_prob", jump_prob[0])
        tf.summary.scalar("value", value[0])
        # collect all summaries up to here for regular state -> policy/value pass-throughs
        summary_get_action = tf.summary.merge_all()

        # from here on: only for worker networks, the master network doesn't really need those
        # TODO: make all this rest a 'module' class

        # prob(action_mapping) = NNsigmoidOut (e.g. 0.8) * actual-action (e.g. 0 or 1) + (1 - NNsigmoidOut)*(1 - actual-action (0 or 1))
        # - calc above prob over all given action-mappings (just 'jump' for now)
        action_probability = pdf.prob(axis_mappings) * (jump_prob * action_mappings + (1 - jump_prob) * (1 - action_mappings))

        # define one single-value loss function (it's a shared policy/value network)
        policy_loss = -(tf.reduce_mean(tf.log(action_probability) * advantage))
        summ_ploss = tf.summary.scalar("policy_loss", policy_loss)
        # −0.5(log(2πσ²) + 1) = -0.5(log(2π * PRODUCT[all axis' variances]) + 1)
        entropy = 0.5 * tf.reduce_mean(tf.log(2 * PI * tf.reduce_prod(forward_turn_var, axis=1)) + 1)
        summ_entropy = tf.summary.scalar("entropy", entropy)
        # DEBUG: juliani has reduce_sum here, but that doesn't make sense as episodes can have different lengths
        value_loss = 0.5 * tf.reduce_mean(tf.square(_R - value))
        summ_vloss = tf.summary.scalar("value_loss", value_loss)

        #DEBUG
        loss = (policy_loss + value_loss - self.beta * entropy)  # no more #num-samples dimension after this (just a single scalar)
        #loss = (value_loss - self.beta * entropy)  # no more #num-samples dimension after this (just a single scalar)
        summ_loss = tf.summary.scalar("loss", loss)

        # get gradients of loss over all parameters
        local_vars = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES)
        gradients = tf.gradients(loss, local_vars)
        # skip gradient clipping for now (introduce when model gets more complicated)
        #var_norms = tf.global_norm(local_vars)
        #grads, grad_norms = tf.clip_by_global_norm(gradients, 40.0)

        return_per_episode = tf.summary.scalar("return_per_episode", episode_orig_return)
        reward_per_step = tf.summary.scalar("reward_per_step", episode_orig_return / len_episode)

        # add extra (required) dims to image
        heatmap_image = tf.expand_dims(heatmap_image, axis=2)  # grey scale
        heatmap_image = tf.expand_dims(heatmap_image, axis=0)  # batch (always just 1 image)
        heatmap_image = tf.summary.image("heatmap_image", heatmap_image)

        summary_train = tf.summary.merge(inputs=[summ_entropy, summ_loss, summ_ploss, summ_vloss, return_per_episode, reward_per_step,
                                                 heatmap_image])

        # TODO: implement shared RMSProp

        # define our outputs
        self.add_outputs(# DEBUG
                         #("cam_expanded", cam_expanded), ("fully_connected_out", fully_connected_out), ("flat_input", flat_input), ("conv2d_out", conv2d_out),
                         ("forward_turn_mean", forward_turn_mean), ("forward_turn_var", forward_turn_var), ("jump_prob", jump_prob), ("value", value),
                         ("policy_loss", policy_loss), ("value_loss", value_loss),
                         ("entropy", entropy), ("loss", loss),
                         ("gradients", gradients),
                         ("summary_get_action", summary_get_action),
                         ("summary_train", summary_train),
                         ("forward_move_out", forward_move_out),
                         ("turn_out", turn_out),
                         ("jump_out", jump_out))

