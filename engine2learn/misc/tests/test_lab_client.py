import socket


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("localhost", 2017))

while True:
    #data = client_socket.recv(1024)
    #if data == 'q' or data == 'Q':
    #    client_socket.close()
    #    break
    #else:
    #print("RECEIVED:", data)
    data = input("SEND(TYPE q or Q to Quit):")
    if data == 'q':
        client_socket.close()
        break
    # reconnect
    elif data == 'r':
        client_socket.close()
        client_socket.connect(("localhost", 2017))
    else:
        client_socket.send(data.encode("utf-8"))

