import socket
import select
import sys

HOST = '127.0.0.1'
PORT = 12344

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.setblocking(False)

try:
    client_socket.connect((HOST, PORT))
except BlockingIOError:
    # Expected since it's non-blocking
    pass

# Use select to wait until the socket is writable (i.e., connected)
_, writable, _ = select.select([], [client_socket], [], 5)
while(1):
    if client_socket in writable:
        message = input("type the message  ")
        print(f"Sending: {message.strip()}")
        client_socket.sendall(message.encode())

    # Use select to wait until the socket is readable
    readable, _, _ = select.select([client_socket], [], [], 5)
    if client_socket in readable:
        response = client_socket.recv(4096)
        print(f"Received: {response.decode().strip()}")

client_socket.close()
