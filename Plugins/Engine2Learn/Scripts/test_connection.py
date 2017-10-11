import socket
import time
import msgpack

print('starting')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 9999))

message = {'one':'two', 'three': [1,2,3,4]}

s.send(msgpack.packb(message))

unpacker = msgpack.Unpacker()

while True:
    print('into loop')
    data = s.recv(8192)
    if not data:
        break
    unpacker.feed(data)
    done = False
    for message in unpacker:
        print(message)
        done = True
    if done:
        break


