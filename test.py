import socket
import select
import random
import threading

HOST = '127.0.0.1'
PORT = 12344

class UniqueRandom:
    def __init__(self, start, end):
        self.pool = list(range(start, end))
        random.shuffle(self.pool)

    def get(self):
        if not self.pool:
            raise ValueError("No more unique numbers left!")
        return self.pool.pop()
class player_progess():
    def __init__(self,fd):
        self.socket= fd
        self.count= 0
        self.time = 0
    def increment(self):
        self.count = self.count + 1
    def add_time(self,time_finished):
        self.time = time_finished
class game_progess():
    def __init__(self,fd):
        self.fd_list = []
        for sock in fd:
            self.fd_list.append(player_progess(sock))
    def incre(self,fd):
        for sock in self.fd_list:
            if sock.socket == fd:
                sock.increment()
            break
    def time(self,fd,time):
         for sock in self.fd_list:
            if sock.socket == fd:
                sock.add_time(time)
            break

def game_room_handle(roomid,message_queue,sockfd_list):
    game = game_progess(sockfd_list)
class game_message():
    def __init__(self,client_socket,message,roomid):
        self.socket = client_socket
        self.msg = message
        self.id  = roomid
class game_message_queue():
    def __init__(self):
        self.queue = []
    def add(self,msg,client_socket,rid):
        self.queue.append(game_message(client_socket,msg,rid))
class player():
    def __init__(self,client_socket,addr):
        self.sock = client_socket
        self.address = addr
        self.in_game = False
        self.in_room = False
        self.host = False
        self.room_id = ""
class playerlist():
    def __init__(self):
        self.list = []
        self.size = 0
    def add(self,user):
        self.list.append(user)
    def check_create_room(self,client_scoket):
        for clients in self.list:
            if clients.sock == client_scoket:
                if clients.in_room == False:
                    clients.in_room = True
                    clients.host = True
                    return 1
                else:
                    return -1
    def check_join_room(self,client_socket):
        for clients in self.list:
            if clients.sock == client_socket:
                if clients.in_room == False:
                    return 1
                else:
                    return -1
    def join_room(self,client_socket,roomid):
        for clients in self.list:
            if clients.sock == client_socket:
                clients.room_id = roomid
    def check_host(self,client_socket):
        for clients in self.list:
            if clients.sock == client_socket:
                if clients.host == True:
                    return clients.room_id
                else:
                    return -1
    def start_game(self,id):
        for clients in self.list:
            if clients.room_id == id:
                clients.in_game = True
class gameroom():
    def __init__(self,host,iden):
        self.host_sock = host
        self.guest_sock =[]
        self.capacity = 4
        self.id = iden
        self.state = -1 # -1 : not ready, 0: ready, 1: game in progess
    def addplayer(self,player):
        self.guest_sock.append(player)
class roomlist():
    def __init__(self):
        self.rlist = []
        self.length = 0
        
    def add(self,room):
        self.rlist.append(room)
    def addguest(self,guest_socket,room_id):
        for room in self.rlist:
            if room.id == room_id:
                room.addplayer(guest_socket)
    
# Create server socket
player_list= playerlist()
room_list= roomlist()
ur = UniqueRandom(0, 10)
msg_queue = game_message_queue()
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()
server_socket.setblocking(False)  # Make server socket non-blocking

# List of sockets to monitor for incoming data
sockets_list = [server_socket]
clients = {}

print(f"Server listening on {HOST}:{PORT}...")

while True:
    # Use select to get sockets ready for reading
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            # New connection
            client_socket, client_address = server_socket.accept()
            client_socket.setblocking(False)
            sockets_list.append(client_socket)
            clients[client_socket] = client_address
            print(f"Accepted new connection from {client_address}")
            player_list.add(player(client_socket,client_address))

        else:
            try:
                data = notified_socket.recv(1024)
                if data:
                    print(f"Received from {clients[notified_socket]}: {data.decode().strip()}")
                    if (data.decode().strip() == "/create room"):
                            temp = player_list.check_create_room(notified_socket)
                            if temp == 1:
                                roomid = ur.get()
                                room_list.add(gameroom(notified_socket,roomid))
                                player_list.join_room(notified_socket,roomid)
                                str = "success create a game room " + str(roomid)
                                notified_socket.sendall(str.encode())
                            if temp == -1: 
                                notified_socket.sendall(b"you already in a game room")
                    if (data.decode().strip() == "/startgame"):
                        roomid = player_list.check_host(notified_socket)
                        if roomid == -1:
                            notified_socket.sendall(b"you are not the host")
                        else:
                            player_list.start_game(roomid)
                            # dont touch this, still in development
                            threading.Thread(target=game_room_handle,args= (roomid,msg_queue,))

                    parts = data.decode().strip().split()
                    if(parts[0] == "/joinroom"):
                        if player_list.check_join_room(notified_socket) == 1:
                            room_list.addguest(notified_socket,parts[1])
                            player_list.join_room(notified_socket,parts[1])
                            notified_socket.sendall(b"joined successfully")
                        else:
                            notified_socket.sendall(b"you already in a room")

                else:
                    # No data — client disconnected
                    print(f"Closed connection from {clients[notified_socket]}")
                    sockets_list.remove(notified_socket)
                    del clients[notified_socket]
                    notified_socket.close()
            except ConnectionResetError:
                print(f"Connection reset by {clients[notified_socket]}")
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                notified_socket.close()

    for err_socket in exception_sockets:
        sockets_list.remove(err_socket)
        err_socket.close()
        del clients[err_socket]
