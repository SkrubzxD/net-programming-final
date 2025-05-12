import socket
import select
import sys

HOST = '127.0.0.1'
PORT = 12344

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.setblocking(False)

class game_room():
    def __init__(self,host,iden):
        self.host_sock = host
        self.guest_sock =[]
        self.capacity = 4
        self.id = iden
        self.state = -1 # -1 : not ready, 0: ready, 1: game in progess
    def addplayer(self,player):
        self.guest_sock.append(player)
    def fdlist(self):
        temp =[]
        temp.append(self.host_sock)
        for sock in self.guest_sock:
            temp.append(sock)
        return temp
    def roomleave(self,clientsocket):
        for client in self.guest_sock:
            if client == client_socket:
                self.guest_sock.remove(client)
            

try:
    client_socket.connect((HOST, PORT))
except BlockingIOError:
    # Expected since it's non-blocking
    pass

# Use select to wait until the socket is writable (i.e., connected)
_, writable, _ = select.select([], [client_socket], [], .1)

while(1):
    if client_socket in writable:
        message = input("Send a message: ")
        if message.strip().lower() == 'exit':
            print("Exiting...")
            break
        elif message.strip() == "":
            continue
        client_socket.sendall(message.encode())

    # Use select to wait until the socket is readable
    readable, _, _ = select.select([client_socket], [], [], .1)
    if client_socket in readable:
        response = client_socket.recv(4096)
        print(f"[Server] {response.decode().strip()}")

client_socket.close()
