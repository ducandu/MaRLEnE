"""
 -------------------------------------------------------------------------
 engine2learn - envs/remote_env.py
 
 An Environment that lives on a remote host. We communicate with this
 RemoteEnv via TCP. `step`/`reset`/etc.. are only network interfaces to
 the remote. The actual implementations and logic of these methods
 live on the remote (e.g. the UE4 game instance).
  
 created: 2017/10/04 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from .base import Env
import socket
import msgpack
import msgpack_numpy as mnp
import errno
import os
from time import time


class RemoteEnv(Env):
    def __init__(self, port=6025, host="localhost"):
        """
        A remote Environment that one can connect to through tcp.
        Implements a simple msgpack protocol to get the step/reset/etc.. commands to the remote server and simply waits (blocks) for a response.
        """
        mnp.patch()  # make all msgpack methods use the numpy-aware de/encoders

        super().__init__()
        self.port = port
        self.host = host
        self.socket = None
        self.buffer_size = 8192  # the size of the response buffer (depends on the Env's observation-space)
        
        self.last_observation = None  # cache the last received observation (through socket) here

    def connect(self):
        """
        Starts the server tcp connection on the given host:port.
        """
        # if we are already connected -> return error
        if self.socket:
            raise RuntimeError("A socket is already connected to {}:{}!".format(self.host, self.port))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        err = self.socket.connect_ex((self.host, self.port))
        if err != 0:
            print("Error when trying to connect to {}:{}: ERRNO={} ERROR={}".format(self.host, self.port, errno.errorcode[err], os.strerror(err)))

    def disconnect(self):
        """
        Ends our server tcp connection.
        """
        # if we are not connected -> return error
        if not self.socket:
            raise RuntimeError("No currently active socket to close!")
        self.socket.close()  # simply close our socket
    
    def send(self, message):
        self.socket.send(msgpack.packb(message))
    
    def recv(self):
        # unpacker = msgpack.Unpacker(encoding="ascii")
        unpacker = msgpack.Unpacker()

        # wait for an immediate response
        response = self.socket.recv(8)
        if response == b"":
            raise RuntimeError("No data received by socket socket.recv in call to method `recv` (connection to {}:{} possibly closed)!".
                               format(self.host, self.port))
        orig_len = int(response)
        recvd_len = 0
        #print("total_len={} sum={}".format(total_len, sum_))
        while True:
            data = self.socket.recv(orig_len - recvd_len)
            #print("data recv'd: len={}".format(len(data)))
            if not data:  # there must be a response
                raise RuntimeError("No data of len {} received by socket.recv in call to method `recv`!".format(orig_len - recvd_len))
            data_len = len(data)
            recvd_len += data_len
            #print("now sum={}".format(sum_))
            unpacker.feed(data)

            if recvd_len == orig_len:
                break
            #total_len -= data_len
            #print("now total_len={}".format(total_len))

        # get the data
        for message in unpacker:
            if "status" in message:
                if message["status"] == "ok":
                    return message
                else:
                    raise RuntimeError("RemoteEnv server error: "+message["message"])
            else:
                raise RuntimeError("Message without field 'status' received!")
        raise RuntimeError("No message encoded in data stream (data stream had len={})")

    def seed(self, seed=None):
        if seed is None:
            seed = int(time())
        # send command
        self.send({"cmd": "seed", "value": seed})
        # wait for response
        response = self.recv()
        if "status" not in response:
            raise RuntimeError("Message without field 'status' received!")
        elif response["status"] != "ok":
            raise RuntimeError("Message 'status' for seed command is not 'ok' ({})!".format(response["status"]))

    def reset(self):
        """
        same as step (no kwargs to pass), but needs to block and return observation_dict
        - stores the received observation in self.last_observation
        """
        # send command
        self.send({"cmd": "reset"})
        # wait for response
        response = self.recv()
        if "obs_dict" not in response:
            raise RuntimeError("Message without field 'obs_dict' received!")
        return response["obs_dict"]

    def step(self, **kwargs):
        """
        Generically just pass all data in **kwargs through the network (after adding "cmd": "step") to the remote and block(!) for an observation_dict response.
        We are assuming local connections and fast executions (single tick). Also, we want to avoid RL-algos to have asynchronous events within themselves.
        """
        if "cmd" in kwargs:
            raise KeyError("Key 'cmd' must not be present in **kwargs to method `step`!")
        
        # forward kwargs to remote (only add command: step)
        message = kwargs
        message["cmd"] = "step"
        self.send(message)
        # wait for response
        response = self.recv()
        if "obs_dict" not in response:
            raise RuntimeError("Message without field 'obs_dict' received!")
        return response["obs_dict"]

    @property
    def action_space(self):
        # RemoteEnv is abstract class
        raise NotImplementedError

    @property
    def observation_space(self):
        # RemoteEnv is abstract class
        raise NotImplementedError

