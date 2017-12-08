from engine2learn.models.base import Model
from engine2learn.modules import FullyConnectedModule, Convolutional2DModule
import sonnet.python.modules.nets as snt_nets
from sonnet.python.modules.nets.convnet import ConvNet2DTranspose
from sonnet import AbstractModule
import sonnet as snt
# from engine2learn.modules.softmax_and_linear_output import SoftmaxAndLinearOutputModule
from math import pi as PI

import tensorflow as tf


class Phi(snt.AbstractModule):
    """
    The feature representation module (phi) of the SR architecture. From image input until before the element-wise multiplication operator.
    """

    def __init__(self, name, **kwargs):
        """
        :param str name: The tensorflow name of the module
        :param any kwargs:
        """
        # generate the model in tensorflow
        self.name = name
        super().__init__(name=name)

    def _build(self, inputs):
        assert inputs.get_shape().as_list() == [None, 86, 86, 4]  # make sure we have the right input shape

        # convolutional module for processing (and flattening) the input signal
        conv2d = snt_nets.ConvNet2D(output_channels=[64, 64, 64],
                                    kernel_shapes=[(6, 6), (6, 6), (6, 6)],
                                    strides=[(2, 2), (2, 2), (2, 2)],
                                    paddings=["SAME", "SAME", "SAME"],
                                    activation=tf.nn.relu,
                                    activate_final=True,
                                    name="phi_conv2d")
        conv2d_out = conv2d(inputs)  # push cam through our conv layers
        # flatten our conv2d output
        flat_from_conv = snt.FlattenTrailingDimensions(dim_from=1, name="phi_conv2d_flat")
        flat_from_conv_out = flat_from_conv(conv2d_out)
        # DEBUG:
        # tf.summary.histogram("cam", cam)
        # tf.summary.histogram("conv2d_out", conv2d_out)
        # tf.summary.histogram("flat_from_conv_out", flat_from_conv_out)
        # tf.summary.histogram("conv2d_weights", conv2d._graph._collections["trainable_variables"][0])
        # tf.summary.histogram("conv2d_biases", conv2d._graph._collections["trainable_variables"][1])
        # tf.summary.scalar("len_episode", len_episode)
        # tf.summary.scalar("goals_reached", goals_reached)
        # tf.summary.scalar("distance_to_goal", distance_to_goal)

        # fully connected module in between flattened in and output softmax (1 layer: input/hidden)
        phi_fc = FullyConnectedModule("phi_fc_module", [1024, 2048], activations=[tf.nn.relu, None])
        phi = phi_fc(flat_from_conv_out)

        return phi


class Psi(snt.AbstractModule):
    """
    The SR-estimator module (psi) of the SR architecture. From learnt image features (phi; flat input) until after the fc-SR-layer (SR-output)
    """
    def __init__(self, name, **kwargs):
        """
        :param str name: The tensorflow name of the module
        :param any kwargs:
        """
        # generate the model in tensorflow
        self.name = name
        super().__init__(name=name)

    def _build(self, inputs):
        assert inputs.get_shape().as_list() == [None, 2048]  # make sure we have the right input shape

        # define the SR module
        no_gradient = tf.stop_gradient(inputs)
        psi_first_relu = tf.nn.relu(no_gradient, name="psi_first_relu_after_stop_gradient")
        psi_fc = FullyConnectedModule("psi_fc_module", [1024, 2048], activations=[tf.nn.relu, None])
        psi = psi_fc(psi_first_relu)

        return psi


class SuccessorReprNetwork(Model):
    """
    A successor state representation model that generates  successor representations for 2D image-based states.
    """
    def __init__(self, name, env, **kwargs):
        """
        :param str name: The name of the model.
        :param engine2learn.Env env: The environment in which this model is used.
        :param any kwargs: more params
        """
        self.num_actions = 6  # hardcode for now: TODO: need to write openAIEnv class wrapper first: env.action_space.shape
        self.learning_rate = kwargs.get("learning_rate", 0.001)
        #self.beta = kwargs.get("beta", 0.0001)  # the weight for the entropy regularizer term (10e-4 according to [1])
        self.optimizer = tf.train.RMSPropOptimizer(learning_rate=self.learning_rate)
        self.gamma = kwargs.get("gamma", 0.99)  # the discount factor gamma for representation learning

        super().__init__(name, **kwargs)

    def construct(self):
        # define our inputs to this graph
        s, s_prime_single_frame, a = self.add_feeds(
            ([None, 86, 86, 4], "s"),  # 4 time steps make up one state description (to be able to capture speed)
            ([None, 86, 86], "s_"),  # the observed(!) single next image (s')
            ([None, self.num_actions], "a")  # the actually chosen action (a) after having observed s
        )
        # construct the complete 4-frame s' for training the SR-net (psi)
        s_ = tf.concat([s[:, :, :, 1:], tf.expand_dims(s_prime_single_frame, axis=3)], axis=3)

        # add action into the network
        fc_action = FullyConnectedModule("fc_module_action", [2048], activations=[None])
        fc_action_out = fc_action(a)

        # generate the training networks
        phi_train = Phi(name="phi_train")
        phi_train_out = phi_train(s)
        psi_train = Psi(name="psi_train")
        psi_train_out = psi_train(phi_train_out)

        # and the target networks
        phi_target = Phi(name="phi_target")
        phi_target_out = phi_target(s)
        psi_target = Psi(name="psi_target")
        psi_target_out = psi_target(phi_target_out)
        # including the pass through of the s'
        phi_target_out_s_ = phi_target(s_)
        psi_target_out_s_ = psi_target(phi_target_out_s_)

        center_node = tf.multiply(phi_train_out, fc_action_out, name="center_multiply")
        zeta_fc = FullyConnectedModule("zeta_fc_module", [1024, 64*10*10], activations=[None, tf.nn.relu])
        zeta_fc_out = zeta_fc(center_node)
        zeta_fc_reshaped = tf.reshape(zeta_fc_out, shape=(-1, 10, 10, 64))
        zeta_deconv = ConvNet2DTranspose(output_channels=[64, 64, 1],
                                         output_shapes=[(20, 20), (40, 40), (86, 86)],
                                         kernel_shapes=[(6, 6), (6, 6), (6, 6)],
                                         strides=[(2, 2), (2, 2), (2, 2)],
                                         paddings=["SAME", "SAME", "SAME"],
                                         activation=tf.nn.relu,
                                         activate_final=False,
                                         name="zeta_conv2dtranspose_module")
        image_out = zeta_deconv(zeta_fc_reshaped)

        # define error functions and training ops
        loss_sr = tf.square(phi_target_out + self.gamma * psi_target_out_s_ - psi_train_out)
        loss_sr = tf.reduce_mean(loss_sr, axis=[0, 1], name="loss_sr")
        loss_re = tf.square(image_out - s_prime_single_frame)
        loss_re = tf.reduce_mean(loss_re)
        loss = loss_sr + loss_re

        train_op = self.optimizer.minimize(loss)

        # define our outputs
        self.add_outputs(("phi_train", phi_train_out), ("psi_train", psi_train_out), ("zeta_image", image_out),
                         ("phi_target", phi_target_out), ("psi_target", psi_target_out),
                         ("loss_sr", loss_sr), ("loss_re", loss_re), ("loss", loss), ("train_op", train_op))

    def update_target(self, sess):
        """
        Updates our target-network (only phi- and psi-target) using the values from our training-network (phi and psi).

        :param tf.Session sess: The tensorflow session to use.
        """
        ops = []
        targets = tf.trainable_variables(scope="target")
        train_vars = tf.trainable_variables(scope="train")
        for source, target in zip(train_vars, targets):
            ops.append(tf.assign(target, source))
        sess.run(ops)

