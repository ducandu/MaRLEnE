"""
 -------------------------------------------------------------------------
 AIOpening - misc/savables.py
 
 A simple class, the state of whose instantiations can be saved to disk.
  
 created: 2017/09/15 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""


class Savable(object):
    def save(self, folder):
        raise NotImplementedError

