"""
 -------------------------------------------------------------------------
 AIOpening - base.py
 
 Space base class (taken from openAI rllab)
  
 created: 2017/09/01 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""


class Space(object):
    """
    Provides a classification state spaces and action spaces,
    so you can write generic code that applies to any Environment.
    E.g. to choose a random action.
    """

    def sample(self, seed=None):
        """
        Uniformly randomly samples an element from this space

        :param int seed: the random seed to use
        :return: the sampled element
        :rtype: any
        """
        raise NotImplementedError

    def contains(self, x):
        """
        Return boolean specifying if x is a valid member of this space

        :param any x: the element to check
        :return:
        :rtype: bool
        """
        raise NotImplementedError

    def flatten(self, x, **kwargs):
        """
        Flattens the given sample from rank n into rank 1 (from nD tensor to 1D vector).

        :param x: the sample to be flattened
        :return: the flattened vector
        :rtype: any
        """
        raise NotImplementedError

    def unflatten(self, x, **kwargs):
        """
        Reshapes a previously flattened sample back into the proper space shape (from 1D vector to nD tensor).

        :param x: the sample to be unflattened
        :return: the reshaped tensor
        :rtype: any
        """
        raise NotImplementedError

    def flatten_batch(self, xs, **kwargs):
        """
        Flattens the given sample after the first axis (the "batch" axis), so from rank n into rank 2 (from nD tensor to 2D vector, where the
        first axis is still the batch axis).

        :param list xs: The list of samples to be batch-flattened.
        :return: The flattened 2D tensor.
        :rtype: any
        """
        raise NotImplementedError

    def unflatten_batch(self, xs, **kwargs):
        """
        Reshapes a previously flattened_batch sample back into the proper space shape, so from rank 2 into rank n (from 2D tensor to nD tensor, where
        the first axis is always the "batch" axis).

        :param list xs: The list of samples to be unflattened.
        :return: The reshaped tensor.
        :rtype: any
        """
        raise NotImplementedError

    @property
    def shape(self):
        """
        The shape of the space (Discrete spaces have shape (n,), where n is the number of discrete states)
        """
        raise NotImplementedError

    @property
    def flat_dim(self):
        """
        The dimension of the flattened vector of the tensor representation
        """
        raise NotImplementedError

    def new_tensor_variable(self, name, extra_dims):
        """
        Create a tensorflow variable given the name and extra dimensions prepended
        :param name: name of the variable
        :param extra_dims: extra dimensions in the front
        :return: the created tensor variable
        """
        raise NotImplementedError
