import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

event_check_room = threading.Event()
class player():
    def __init__(self,client_socket,addr):
        self.sock = client_socket
        self.address = addr
class playerlist():
    def __init__(self):
        self.list = []
        self.size = 0
    def add(self,user):
        self.list.append(user)
class gameroom():
    def __init__(self,host,iden):
        self.host = host
        self.guest =[]
        self.capacity = 4
        self.id = iden
        self.state = -1 # -1 : not ready, 0: ready, 1: game in progess
    def addplayer(self,player):
        self.guest.append(player)
class roomlist():
    def __init__(self):
        self.rlist = []
        self.length = 0
        
    def add(self,room):
        self.rlist.append(room)
    def find_state(self):
        for room in self.rlist:
                if room.state == 0:
                    return room.id

def handle_client(client_socket, address):
    print(f"Connected to {address}")
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break  # client disconnected
            print(f"Received from {address}: {data.decode().strip()}")
            client_socket.sendall(data)  # echo back
    except ConnectionResetError:
        print(f"Connection reset by {address}")
    finally:
        client_socket.close()
        print(f"Closed connection to {address}")
def handle_roomlist(roomarr):
    
    while(1):
        event_check_room.wait()
        state = roomarr.find_state()
        # another thread to handle the game here

def main():
    client_list = playerlist()
    roomarr = roomlist()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Server listening on {HOST}:{PORT}")

    while True:
        client_sock, addr = server_socket.accept()
        # Pass the client socket (FD) to a new thread
        playerlist.add(player(client_sock,addr))
        thread = threading.Thread(target=handle_client, args=(client_sock, addr))
        thread.start()

if __name__ == "__main__":
    main()
