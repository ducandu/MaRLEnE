"""
 -------------------------------------------------------------------------
 AIOpening - models/base.py
 
 Defines a simple base Model used for approximating functions.
  
 created: 2017/09/01 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

import sonnet as snt
import tensorflow as tf
import re
import os
import pickle


class Model(object):
    """
    A Model is a container for one or more sonnet Modules that - put together - form a certain NN topology (a tf.Graph).
    It offers easy Module-assembly code (to assemble and re-assemble its Graph), to train the model and to predict outputs by
    running inputs through the graph (without training).
    """
    def __init__(self, name, **kwargs):
        self.name = name
        # the directory in which all information about this model is saved
        self.directory = kwargs.get("directory", re.sub(r"\W", "", name))  # type: str
        if not re.search(r"[/\\]$", self.directory):  # add trailing slash to path
            self.directory += "/"
        # create our directory
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.modules = kwargs.get("modules", {})
        self._feeds = kwargs.get("feeds", {})  # all input feeds (usually tf.placeholders) for this model are collected here by their tensor name
        self._outputs = {}  # the dict with all important output tensors of this model (e.g. logits, cost, predictions, train_op, accuracy, etc..)
        self._saver = None  # the tf.Saver object for the graph
        self.num_trainable_variables = 0

        # this will construct the entire graph
        self.reset()

    def construct(self):
        """
        Rebuilds the tf.Graph from scratch into the tensorflow default_graph.
        This method needs to be overridden by all children of this Model class.
        """
        raise NotImplementedError

    def add_module(self, module_):
        assert module_.name not in self.modules, "ERROR: module with name {} already in our module list!".format(module_.name)
        assert isinstance(module_, snt.AbstractModule), "ERROR: given module is not of type sonnet.AbstractModule (but of type: {})!".\
            format(type(module_).__name__)
        self.modules[module_.name] = module_

    def add_feeds(self, *feeds):
        """
        Adds placeholders (feeds) to the Module.

        :param list feeds: The list of feeds to create tf.placeholder objects from.
        Feeds are specified via a list of tuples, where each tuple has the following format:
        0=tf dtype; 1=shape (list or tuple); 2=name (without the tf ':0'-part)
        :return: A tuple containing all placeholder objects that were created in the same order as the *feeds list.
        :rtype: tuple
        """
        ret = []
        for feed in feeds:
            assert isinstance(feed, tuple) or isinstance(feed, list), "ERROR: Given feed ({}) is not a tuple (shape, name[, dtype])!".format(feed)
            # dtype missing -> use tf.float32
            if len(feed) == 2:
                typ = tf.float32
            else:
                typ = feed[2]
            #assert name not in self._feeds, "ERROR: feed with name {} already in our feed list!".format(name)
            placeholder = tf.placeholder(dtype=typ, shape=feed[0], name=feed[1])
            self._feeds[feed[1]] = placeholder
            ret.append(placeholder)
        return tuple(ret)

    def get_feed(self, name):
        """
        Returns an input feed (placeholder) by name.

        :param str name: The name under which the input feed is kept in our dict.
        :return: The tf.placeholder object stored under the given name.
        :rtype: tf.placeholder
        """
        return self._feeds[name]

    def add_outputs(self, *outputs):
        """
        Adds outputs (as tf.Tensor/Operation or as a dict with "name" and "list" fields (=list of Tensors/Operations)) to this Module.

        :param list outputs: The list of output tf.Tensors (that are already created!). The name under which these outputs are stored
        in our dict are derived from the Tensor's name (without the ":..." part)
        """
        for output in outputs:
            assert isinstance(output, tuple) or isinstance(output, list), "ERROR: Given output ({}) is not a tuple (shape, name[, dtype])!".format(output)
            name = output[0]
            list_or_tensor = output[1]
            assert isinstance(list_or_tensor, tuple) or isinstance(list_or_tensor, list) or\
                isinstance(list_or_tensor, tf.Tensor) or isinstance(list_or_tensor, tf.Operation),\
                "ERROR: Given output ({}) is not a tuple/list/Tensor/Operation!".format(output)
            self._outputs[name] = list_or_tensor

    def get_output(self, name):
        """
        Returns a tf.Tensor object for the given name.

        :param str name: The name of the Tensor, which we would like to get returned.
        :return: The Tensor that is stored under the given name in our dict.
        :rtype: tf.Tensor
        """
        return self._outputs.get(name, None)

    def add_fork(self, from_, to_left, to_right):
        """
        Adds a fork topology to a network connecting three modules, one incoming, two outgoing ("left" and "right")
        :param from_:
        :type from_:
        :param to_left:
        :type to_left:
        :param to_right:
        :type to_right:
        :return:
        :rtype:
        """
        pass

    def add_concat(self):
        pass

    def reset(self):
        """
        Completely resets the Model (graph) to an empty graph, then rebuilds the graph (all variables' values will be wiped out)
        by calling the build method.
        """
        tf.reset_default_graph()
        # reconstruct our graph
        self.construct()
        self._saver = tf.train.Saver()

        self.count_num_trainable()

        print("Model reset and reconstructed: size={}".format(self.num_trainable_variables))

    def count_num_trainable(self):
        """
        Counts the number of trainable tf.Variables to get a rough idea of how complex this Model is

        :return: Number of trainable tf.Variables in the tf.Graph
        :rtype: int
        """
        self.num_trainable_variables = 0
        for variable in tf.trainable_variables():
            # shape is an array of tf.Dimension
            shape = variable.get_shape()
            variable_parameters = 1
            for dim in shape:
                variable_parameters *= dim.value
            self.num_trainable_variables += variable_parameters

        return self.num_trainable_variables

    def save_topology(self):
        """
        Saves the topology of the Model (the tf.Graph) to disk.
        """
        tf.train.export_meta_graph(filename=self.directory + "graph")

    def save_params(self, session):
        """
        Saves all variables of our graph (the tf.Graph) to disk.

        :param tf.Session session: The tensorflow Session object we currently have open.
        """
        self._saver.save(session, self.directory + "graph")

    def load_params(self, session, get=False, initialize=True):
        """
        Loads all variables of our graph (the tf.Graph) from disk.

        :param tf.Session session: The tensorflow Session object where the default graph will be loaded.
        :param bool get: Whether we should return the loaded weights as bytes using the get_params method.
        :param bool initialize: Whether we should initialize the model if no snapshot found on disk.
        """
        # load saved model params from disk
        if os.path.exists(self.directory + "graph"):
            self._saver.restore(session, self.directory + "graph")
            if get:
                return self.get_params(session)
        # simply initialize the model
        elif initialize:
            session.run(tf.global_variables_initializer())
            if get:
                return self.get_params(session)

    @staticmethod
    def get_params(session):
        """
        Returns the values of the entire graph as a serialized object. This can then be used to pass things around between different worker processes.

        :param tf.Session session: The tensorflow Session object we currently have open.
        :return: The serialized object containing all Variable values.
        :rtype: bytes
        """
        return pickle.dumps(session.run(tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES)))

    @staticmethod
    def set_params(session, bytes_):
        """
        Assigns the given (pickle-serialized) values to the entire graph. This can be used to restore values in memory or through a pipe without
        having to use the file system.

        :param tf.Session session: The tensorflow Session object we currently have open.
        :param bytes bytes_: The pickle.dump'ed bytes object holding all the Graph's Variable values.
        """
        # the actual new values (in the right order)
        values = pickle.loads(bytes_)
        # the tf.Variable objects that need to get the assignments (to the new values)
        variables = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES)

        # make sure the two lists have the same length
        assert len(values) == len(variables)

        exec_list = [variable.assign(value) for variable, value in zip(variables, values)]
        # run all assignments inside the session
        session.run(exec_list)

