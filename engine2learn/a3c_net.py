from engine2learn.models.base import Model
from engine2learn.modules.fully_connected_module import FullyConnectedModule
from engine2learn.modules.softmax_and_linear_output import SoftmaxAndLinearOutputModule
import tensorflow as tf


class A3CPolicyNetwork(Model):
    """
    A policy network used by this example:
    Basic fully connected NN with two output "sections", one softmax layer for the action probabilities (policy),
    one single linear output for the state value prediction.
    """
    def __init__(self, name, num_inputs, num_hidden, num_actions, **kwargs):
        self.num_inputs = num_inputs
        self.num_hidden = num_hidden
        self.num_actions = num_actions
        #self.learning_rate =
        self.beta = kwargs.get("beta", 0.01)  # the weight for the entropy regularizer term
        self.optimizer = tf.train.RMSPropOptimizer(learning_rate=0.01)

        super().__init__(name, **kwargs)

    def construct(self):
        # define our inputs to this graph
        s, a, _R, advantage = self.add_feeds([
            ([None, self.num_inputs], "s"),  # the input (state) signal
            # used to calculate loss of policy function
            ([None], "a", tf.int32),  # the action that got selected as a single int value
            ([None], "advantage"),  # the calculated advantage (fed in separately, b/c we don't want the V-term within advantage to change the policy weights)
            # used to calculate loss of the value function
            ([None], "R"),  # the target (true discounted return) for our value function
        ])

        # fully connected module (1 layer: input/hidden)
        fc = FullyConnectedModule("fc_module", [self.num_hidden], activations=tf.nn.relu)
        fc_out = fc(s)

        # squeeze output through: policy output and value function
        soft_linear = SoftmaxAndLinearOutputModule("soft_linear", self.num_actions + 1, 1)
        policy, value = soft_linear(fc_out)
        value = tf.reshape(value, [-1])  # make value just rank=1 (1 scalar value per batch item)

        # from here on: only for worker networks, the master network doesn't really need those
        # TODO: make all this rest a 'module' class

        # which action actually got picked ('a' is placeholder!)?
        action_onehot = tf.one_hot(a, self.num_actions, dtype=tf.float32)
        # the pure probability of the picked action (output of pi(a,s))
        action_probability = tf.reduce_sum(policy * action_onehot, [1])

        # define one single-value loss function (it's a shared policy/value network)
        policy_loss = - tf.reduce_sum(tf.log(action_probability) * advantage)
        entropy = - tf.reduce_sum(policy * tf.log(policy))
        value_loss = 0.5 * tf.reduce_sum(tf.square(_R - value))
        loss = policy_loss - self.beta * entropy + value_loss  # no more #num-samples dimension after this (just a single scalar)

        # get gradients of loss over all parameters
        local_vars = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES)
        gradients = tf.gradients(loss, local_vars)
        # skip gradient clipping for now (introduce when model gets more complicated)
        #var_norms = tf.global_norm(local_vars)
        #grads, grad_norms = tf.clip_by_global_norm(gradients, 40.0)

        # TODO: implement shared RMSProp

        # define our outputs
        self.add_outputs([("policy", policy), ("value", value), ("policy_loss", policy_loss),
                          ("entropy", entropy), ("value_loss", value_loss), ("loss", loss), ("gradients", gradients)])
