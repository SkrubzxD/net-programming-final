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
    pass

# Wait for the server to ask for the username
while True:
    readable, _, _ = select.select([client_socket], [], [], 5)
    if client_socket in readable:
        response = client_socket.recv(4096)
        if response:
            print(response.decode().strip())
            if "Please enter your username" in response.decode():
                username = input().strip()
                client_socket.sendall(username.encode())
                break
        else:
            print("Server closed the connection.")
            client_socket.close()
            sys.exit()

# Main loop for sending and receiving messages
while True:
    try:
        # Use select to check for both server messages and user input
        readable, _, _ = select.select([client_socket, sys.stdin], [], [])
        if client_socket in readable:
            response = client_socket.recv(4096)
            if response:
                print(response.decode().strip())
            else:
                print("Server closed the connection.")
                break

        if sys.stdin in readable:
            message = sys.stdin.readline().strip()
            if message:
                client_socket.sendall(message.encode())

    except KeyboardInterrupt:
        print("\nDisconnected from the server.")
        break
    except ConnectionResetError:
        print("Connection reset by the server.")
        break

client_socket.close()
