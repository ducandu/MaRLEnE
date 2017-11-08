"""
 -------------------------------------------------------------------------
 AIOpening - modules/convolutional_nn.py
 
 A convolutional module contains one or many convolutional layers
 with the options of max-pooling layers in between the conv-layers
  
 created: 2017/09/04 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

import sonnet as snt
import tensorflow as tf
from engine2learn.misc.helper import list_of_lists


class Convolutional2DModule(snt.AbstractModule):
    """
    A multi-layer convolutional network with - possibly - intermittent max-pooling layers.
    """

    def __init__(self, name, **kwargs):
        """
        Apply convolutions - alternating - with max-pooling.
        The kwargs parameters output_channels til batch_norm_config can be looked up here:
        https://github.com/deepmind/sonnet/blob/master/sonnet/python/modules/nets/convnet.py

        :param str name: The name of the sonnet Module
        :param any kwargs: any parameters that can be sent to snt.convnet.ConvNet2D plus:
        pool_k_sizes: Kernel size 2-D Tuples (one for each layer) for pooling.
        pool_strides: Stride 2-D Tuple (one for each layer) for pooling.
        """

        self.config = kwargs

        # generate the model in tensorflow
        self.name = name
        super().__init__(name=name)

    def _build(self, inputs):
        """
        Builds the _graph according to the config (kwargs) given in __init__
        Applies convolution then - maybe - max pooling to inputs.

        :param inputs: The input tensor to this module (usually the image).
        :return: The output tensor of the Module
        :rtype: tf.Tensor
        """

        output_channels = self.config.get("output_channels", 32)

        # only a single layer? -> make output_channels a list so we know how many layers we need
        if isinstance(output_channels, int):
            output_channels = [output_channels]

        # how many layers do we want? (1 "layer" = 1 conv + 0 or 1 max-pool)
        num_layers = len(output_channels)

        kernel_shapes = list_of_lists(self.config.get("kernel_shapes", None), num_layers, (8, 8))
        strides = list_of_lists(self.config.get("strides", None), num_layers, (1, 1))
        paddings = self.config.get("paddings", None)
        activations = self.config.get("activations", None)
        initializers = self.config.get("initializers", None)
        # TODO:
        # partitioners = self.config.get("partitioners", None)
        # regularizers = self.config.get("regularizers", None)
        # use_batch_norm = self.config.get("use_batch_norm", False)
        # batch_norm_config = self.config.get("batch_norm_config", None)
        use_bias = self.config.get("use_bias", True)

        max_pooling = self.config.get("max_pooling", False)
        pool_k_sizes = list_of_lists(self.config.get("pool_k_sizes", None), num_layers, (2, 2))
        pool_strides = list_of_lists(self.config.get("pool_strides", None), num_layers, (1, 1))
        pool_paddings = self.config.get("pool_paddings", None)

        ## do some sanity checking
        ##assert len(kernel_shapes) == 1 or len(kernel_shapes) == num_layers, "ERROR: kernel_shapes does not have correct format!"

        prev_out = inputs

        for layer in range(num_layers):
            # input shape=[#sam x width x height x depth]
            # get the input depth (the 4th slot of the shape of the input volume (#samples x w x h x in-depth))
            depth = prev_out.get_shape().as_list()[3]
            # create a 4D weight volume (w x h x in-depth x out-depth) where usually w==h
            kernel_shape = kernel_shapes[layer]
            initializer = tf.truncated_normal_initializer(stddev=0.01) if initializers is None\
                else initializers[0] if len(initializers) == 1 else initializers[layer]
            weights = tf.get_variable("conv_weights", shape=(kernel_shape[0], kernel_shape[1], depth, output_channels[layer]),
                                      initializer=initializer, dtype=tf.float32)
            biases = None
            if use_bias:
                # biases are just 1D vectors: shape=[out-depth]
                biases = tf.get_variable("conv_biases", shape=(output_channels[layer],), initializer=initializer, dtype=tf.float32)

            # build our conv layer and add the bias (w/h strides given by function params, other strides (samples and in-depth) are always 1)
            strides = strides[layer]
            padding = "SAME" if paddings is None else paddings[0] if len(paddings) == 1 else paddings[layer]
            conv = tf.nn.conv2d(prev_out, weights, [1, strides[0], strides[1], 1], padding)
            if use_bias:
                conv = tf.nn.bias_add(conv, biases)
            # add non-linearity
            activation = tf.nn.relu if activations is None else activations[0] if len(activations) == 1 else activations[layer]
            conv = activation(conv)
            # max pool to compress the image (if pool_strides > 1)
            if max_pooling:
                pool_k_size = pool_k_sizes[layer]
                pool_stride = pool_strides[layer]
                pool_padding = "SAME" if pool_paddings is None else pool_paddings[0] if len(pool_paddings) == 1 else pool_paddings[layer]
                conv = tf.nn.max_pool(conv, ksize=[1, pool_k_size[0], pool_k_size[1], 1], strides=[1, pool_stride[0], pool_stride[1], 1], padding=pool_padding)

            prev_out = conv

        return prev_out

