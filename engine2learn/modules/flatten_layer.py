"""
 -------------------------------------------------------------------------
 AIOpening - modules/flatten_layer.py
 
 Provides a simple flattening op useful e.g. to go from a conv2D layer
  into a fully connected one.
  
 created: 2017/09/04 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

import sonnet as snt
import tensorflow as tf


class FlattenLayer(snt.AbstractModule):
    """
    A simple flatten module (can be put between conv2d and fully connected).
    """

    def __init__(self, name): #, keep_axis=1):
        """
        Apply convolutions - alternating - with max-pooling.
        The kwargs parameters output_channels til batch_norm_config can be looked up here:
        https://github.com/deepmind/sonnet/blob/master/sonnet/python/modules/nets/convnet.py

        :param str name: The name of the sonnet Module
        e.g. keep_axis=-1: flatten everything except very last axis
        keep_axis=None means: flatten everything.
        """

        #:param int keep_axis: The axis which will be exempt from flattening (can only be one at most). If keep_axis is negative, we will count from the end.
        #self.keep_axis = keep_axis

        # generate the model in tensorflow
        self.name = name
        super().__init__(name=name)

    def _build(self, inputs):
        """
        Does the flattening operation depending on the given input.

        :param inputs: The input tensor to this module (e.g. a conv2D output).
        :return: The output tensor of the Module
        :rtype: tf.Tensor
        """

        # calculate how many slots we need from the 3 dimensions of the incoming conv layer (filter w/h plus depth)
        dims = inputs.get_shape().as_list()
        new_dim = 1
        for d in dims[1:]:  # leave first axis as is (batch)
            new_dim = new_dim * d  # multiply 'em up
        return tf.reshape(inputs, [-1, new_dim])  # -1=keep this dimension as is (it could be anything as this is the number of samples) and flatten the others

