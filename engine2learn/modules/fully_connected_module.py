"""
 -------------------------------------------------------------------------
 AIOpening - feed_forward_module.py
 
 A simple fully-connected feed-forward NN module
  
 created: 2017/08/31 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

import sonnet as snt


class FullyConnectedModule(snt.AbstractModule):
    """
    A multi-layer perceptron (simple feed forward neural net with n hidden layers with [m, o, p, ...] hidden nodes each).
    The number of input and output nodes can be determined by the optional env_spec (observation (input) and action (output) spaces)
    """

    def __init__(self, name, num_nodes=(32,), **kwargs):
        """
        :param str name: The tensorflow name of the module
        :param List[int] num_nodes: A tuple or list containing the number of nodes to use for each layer (except input layer)
        :param any kwargs:
        env_spec (aiopening.envs.EnvSpec): The EnvSpec to use to determine the output layer (action_space + softmax).
        activations (list): A list of activation functions to use for each layer.
        - If env_spec is given, the last layer will be passed through a softmax).
        - If None or some item in the list is None: No activation function will be used for all/this layer.
        """
        # generate the model in tensorflow
        self.name = name
        super().__init__(name=name)

        # if env_spec is given -> derive the number of output nodes from the action space
        #env_spec = kwargs.get("env_spec", None)
        self._num_nodes = num_nodes
        self._num_layers = len(self._num_nodes)
        self._activations = kwargs.get("activations", None)
        # a single activation function is given -> apply this one to all layers
        if not isinstance(self._activations, list):
            self._activations = [self._activations] * self._num_layers

        #if env_spec is not None:
        #    action_space = env_spec.action_space
        #    self._num_nodes.append(action_space.flat_dim)
        #    # do a softmax on the output actions to make it a distribution
        #    if self._activations is not None:
        #        if len(self._activations) < len(self._num_nodes):
        #            self._activations.append(tf.nn.softmax)
        #    else:
        #        self._activations = [None for n in range(len(self._num_nodes))]

    def _build(self, inputs):
        prev_out = inputs
        for i, (activation, num_hid) in enumerate(zip(self._activations, self._num_nodes)):
            h_to_h = snt.Linear(output_size=num_hid, name="hid_{:02d}".format(i))
            if activation is not None:
                prev_out = activation(h_to_h(prev_out))
            else:
                prev_out = h_to_h(prev_out)

        return prev_out

