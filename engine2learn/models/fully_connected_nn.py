"""
 -------------------------------------------------------------------------
 AIOpening - models/fully_connected_model.py
 
 A fully connected feed-forward NN with n hidden layers.
  
 created: 2017/09/08 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from engine2learn.models.base import Model
from engine2learn.modules.fully_connected_module import FullyConnectedModule
import tensorflow as tf


class FullyConnectedNN(Model):
    def __init__(self, name, nodes, activations=None, **kwargs):
        """
        Takes a list of nodes (input, hidden1, hidden2, ..., output) and constructs a fully connected NN from that.

        :param str name: see parent
        :param list nodes: The list/tuple of nodes to use to construct this fully connected network (num inputs, num hidden1, num hidden2, etc.., num outputs).
        :param list activations: The list of activation functions to use from the first hidden layer until the output layer.
        :param any kwargs: see parent
        """
        self.nodes = nodes
        self.num_layers = len(nodes)
        self.activations = activations
        # self.optimizer = optimizer or tf.train.AdamOptimizer()

        super().__init__(name, **kwargs)

    def construct(self):
        # define our two inputs to this graph (x (inputs) and y (labels))
        x, y = self.add_feeds([([None, self.nodes[0]], "x"), ([None, self.nodes[-1]], "y")])

        # only one Module needed
        fc = FullyConnectedModule("fc_module", self.nodes[1:], activations=self.activations)
        logits = fc(x)

        # Loss and Optimizer
        cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=y), name="cost")
        #train_op = self.optimizer.minimize(cost, name="train_op")  # set this model's train operation

        # predictions
        predictions = tf.argmax(logits, 1, name="predictions")  # 1=axis 1 (0 is the batch)

        # Accuracy
        correct_predictions = tf.equal(tf.argmax(logits, 1), tf.argmax(y, 1))  # this will be true or false values
        # casting true/false will result in 0.0/1.0, respectively
        # the mean of these 0.0 or 1.0 over all samples will give the accuracy over all samples
        accuracy = tf.reduce_mean(tf.cast(correct_predictions, tf.float32), name="accuracy")

        self.add_outputs([("logits", logits), ("cost", cost), ("predictions", predictions), ("accuracy", accuracy)])
