"""
 -------------------------------------------------------------------------
 AIOpening - modules/policy_value_output.py
 
 A Module consisting of a single (output) layer that's softmaxed
 over all inputs (policy), except for one single
 linear output (value function)
  
 created: 2017/09/11 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

import sonnet as snt
import tensorflow as tf


class SoftmaxAndLinearOutputModule(snt.AbstractModule):
    """
    A single layer that outputs n softmaxed logits plus m linear (non-softmaxed) outputs (e.g. value-function: m=1).
    """

    def __init__(self, name, num_nodes, m=1, **kwargs):
        """
        :param str name: The tensorflow name of the module
        :param int num_nodes: The number of nodes (altogether) in the layer.
        :param int m: The number of nodes that should not be softmaxed.
        :param any kwargs:
        """
        self.name = name
        super().__init__(name=name)

        self.num_nodes = num_nodes
        self.m = m

    def _build(self, inputs):
        shape = inputs.get_shape().as_list()
        assert len(shape) == 2, "ERROR: input is not of shape (#-samples, feature)!"

        # add 1 fully connected layer
        softmax_layer = snt.Linear(output_size=self.num_nodes - self.m, name="softmax")
        linear_layer = snt.Linear(output_size=self.m, name="linear")

        softmax_out= tf.nn.softmax(softmax_layer(inputs), name="logits_softmaxed")
        linear_out = tf.identity(linear_layer(inputs), name="logits_linear")

        return softmax_out, linear_out

