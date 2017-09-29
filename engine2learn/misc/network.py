"""
 -------------------------------------------------------------------------
 AIOpening - misc/network.py
 
 Implements a simple TCP/IP listen server for usage in our remote classes.
  
 created: 2017/09/07 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

import socket
import threading
import queue
from io import StringIO
import paramiko
from scp import SCPClient


class SshClient:
    """
    A wrapper of paramiko.SSHClient
    """
    TIMEOUT = 4

    def __init__(self, host, port, username, password, key=None, passphrase=None):
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key is not None:
            key = paramiko.RSAKey.from_private_key(StringIO(key), password=passphrase)
        self.client.connect(host, port, username=username, password=password, pkey=key, timeout=self.TIMEOUT)
        # provide an easy scp functionality (get/put interface for transferring files over ssl)
        self.scp = SCPClient(self.client.get_transport())

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None

    def execute(self, command, sudo=False):
        """
        Executes a remote command

        :param str command: The command to run on the remote server.
        :param bool sudo: Whether to run this command via `sudo` for user root.
        """
        feed_password = False
        if sudo and self.username != "root":
            command = "sudo -S -p '' %s" % command
            feed_password = self.password is not None and len(self.password) > 0
        stdin, stdout, stderr = self.client.exec_command(command)
        if feed_password:
            stdin.write(self.password + "\n")
            stdin.flush()
        return {'out': stdout.readlines(),
                'err': stderr.readlines(),
                'retval': stdout.channel.recv_exit_status()}


# Test program
if __name__ == "__main__":
    client = SshClient(host='host', port=22, username='username', password='password')
    try:
        ret = client.execute('dmesg', sudo=True)
        print("  ".join(ret["out"]), "  E ".join(ret["err"]), ret["retval"])
    finally:
        client.close()



"""# Test program
if __name__ == "__main__":
    while True:
        port_num = input("Port? ")
        try:
            port_num = int(port_num)
            break
        except ValueError:
            pass

    # start an experiment server and listen on a socket
    ExperimentServer(port_num)

"""