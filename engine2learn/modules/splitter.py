"""
 -------------------------------------------------------------------------
 engine2learn - modules/splitter.py
 
 created: 2017/10/11 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

import sonnet as snt
import tensorflow as tf


class SplitterModule(snt.AbstractModule):
    """
    A splitter module splits an incoming input into n sub-tensors and applies
    an activation to each of these sub-tensor.
    """

    def __init__(self, name, splits, axis=1, activations=None):
        """
        :param str name: The tensorflow name of the module
        :param List[int] splits: A tuple or list containing the number of nodes to use for each sub-tensor
        :param int axis: The axis to split along.
        :param List[tf.Operator] activations: A list of activation functions to apply to each split (if only one element -> apply to all)
        """
        # generate the model in tensorflow
        self.name = name
        super().__init__(name=name)

        # if env_spec is given -> derive the number of output nodes from the action space
        self._num_layers = len(splits)
        self._splits = splits
        self._axis = axis
        self._activations = activations
        # a single activation function is given -> apply this one to all layers
        if not isinstance(self._activations, list):
            self._activations = [self._activations] * self._num_layers

    def _build(self, inputs):
        sub_tensors = tf.split(inputs, num_or_size_splits=self._splits, axis=self._axis)
        # apply given activations to each sub-split
        outs = []
        for activation, tensor in zip(self._activations, sub_tensors):
            outs.append(activation(tensor) if activation is not None else tensor)

        return tuple(outs)

