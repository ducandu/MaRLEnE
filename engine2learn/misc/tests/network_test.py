import aiopening as ai
from aiopening.misc.network import SimpleServer
import multiprocessing


# TODO: bad name
class Experimenter(object):
    def __init__(self, host="localhost", port=2017, num_jobs=1):
        self.host = host
        self.port = port
        self.num_jobs = num_jobs

        # a copy of the original Experiment that is in control of this Experimenter
        # - this is used to know, what to do if the "start" signal comes from the Lab/Experiment
        self._experiment = None

        self.queue = multiprocessing.Queue()

        self._clients = {}  # a dict of our connected clients
        self._jobs = {}  # a dict of our spawned off jobs

        # create server and start the server listening thread
        self.server = SimpleServer(host, port, self.queue)
        self.server_process = multiprocessing.Process(target=self.server_process, args=(self.server,))
        self.server_process.start()

        # this will block
        self.experiment()

        # is this necessary?
        self.server_process.join()

    @staticmethod
    def server_process(server):
        """
        Starts our server module (listen for Lab/Experiment clients).
        Needs to run in a separate process, b/c it'll block execution.
        """
        server.listen()

    def experiment(self):
        """
        Listen on our Queue for incoming commands from the Lab/Experiment client(s)
        """
        while True:
            command = self.queue.get()
            assert isinstance(command, dict)
            code = command.get("command")
            # a new client command:
            if code == "new_client":
                # add new client's command queue to our list (so we can send it back stuff)
                print("got command from queue: new client")
                client = command.get("client")
                assert client not in self._clients
                q = command.get("queue")
                assert isinstance(q, multiprocessing.Queue)
                self._clients[client] = q
            # parrot command -> parrot text back
            elif code == "parrot":
                print("got command from queue: parrot")
                client = command.get("client")
                text = command.get("text", "[nothing]")
                self._clients[client].put(text)
            else:
                raise TypeError("***ERROR: command `{}` not supported!".format(code))
            # TODO: do something with _experiment here


# test program
if __name__ == "__main__":
    # this will block?
    dude = Experimenter()


