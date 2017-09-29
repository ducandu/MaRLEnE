"""
 -------------------------------------------------------------------------
 AIOpening - misc/protocol.py
 
 The command protocols used to:
 - handle communication between Experiments
 (in Lab objects) and spawned off Executor objects that run in their own
 processes/threads.
 - handle communication between Executors and their spawned off Algorithm
 objects

 created: 2017/09/06 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""


class Message(object):
    def __init__(self, message):
        pass