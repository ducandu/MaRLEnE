"""
 -------------------------------------------------------------------------
 engine2learn - 
 sonnet_test.py
 
 !!TODO: add file description here!! 
  
 created: 2017/12/07 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

import sonnet as snt
import numpy as np
import tensorflow as tf

# Provide your own functions to generate data Tensors.
inputs = tf.constant([[1, 2, 3, 4,  5]], dtype=tf.float32)
target = tf.constant([[5, 6, 1, 8, 10]], dtype=tf.float32)

# Construct the module, providing any configuration necessary.
mod1 = snt.Linear(output_size=10, name="module")

out1 = mod1(inputs)
out2 = mod1(target)

with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    o1, o2 = sess.run([out1, out2])

print(o1+"\n"+o2)

