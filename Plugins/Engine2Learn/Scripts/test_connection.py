import socket
import time
import msgpack

print('starting')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 9999))

message = {'cmd':'step'}

s.send(msgpack.packb(message))

message = {'cmd':'reset'}

s.send(msgpack.packb(message))

message = {'cmd':'step', 'delta_time': 0.33}

s.send(msgpack.packb(message))

message = {'cmd':'step', 'delta_time': 0.33,
             'keys': [{'name': 'X', 'pressed': True}, {'name': 'Y', 'pressed': False}],
             'axis': [{'name': 'Left', 'delta': 1}, {'name': 'Right', 'delta': 0}]
          }

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


