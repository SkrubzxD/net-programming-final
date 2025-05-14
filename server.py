import socket
import select
import random
import threading
import time

def send_menu(fd, player_list):
    main_menu = """\n
---------------------
|        HOME       |
| 1. create room    |
| 2. join room      |
| 3. list room      |
| x. leave game     |
---------------------
"""
    game_menu_guest = """\n
---------------------
|       ROOM        |
| 1. start          |
| 2. chat           |
| x. leave room     |    
---------------------
"""
    game_menu_host = """\n
---------------------
|    ROOM (HOST)    |  
| 1. start          |
| 2. chat           |
| x. disban         |
---------------------
"""
    player = player_list.get_player(fd)
    if not player.in_room:
        return main_menu
    else:
        if not player.in_game and player_list.check_host(fd) == -1:
            return game_menu_guest
        elif not player.in_game and player_list.check_host(fd) != -1:
            return game_menu_host

HOST = '127.0.0.1'
PORT = 12344

event_finished_game = threading.Event()


def finished_game(player_list,room_list,msg_queue):
    while (1):
        for msg in msg_queue.finised_queue :
            player_list.finised_game(msg)
            room_list.game_done(msg)
            msg_queue.remove_special_msg(msg)
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
        self.guess_in_time = -1
    def increment(self):
        self.count = self.count + 1
    def add_time(self,time_finished):
        self.time = time_finished
        self.guess_in_time = 1
    def finished(self):
        self.socket.sendall(b"time up !!!")
    def point_cal(self):
        if self.guess_in_time == 1:
            return 0
        else:
            base = 100
            speed_bonus = max(0, int(100 - self.time))
            guess_penalty = self.count * 5
            return max(0, base + speed_bonus - guess_penalty)
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
    def time_up(self):
        for player in self.fd_list:
            player.finished()
    def announce_results(self):
    # Step 1: Create a list of tuples (score, player)
        scores = []
        for player in self.fd_list:
            score = player.point_cal()
            scores.append((score, player))

        # Step 2: Sort by score descending
        scores.sort(reverse=True, key=lambda x: x[0])

        # Step 3: Send rank and score to each player
        for rank, (score, player) in enumerate(scores, start=1):
            send_menu_msg = send_menu(player.socket, player_list)
            message = f"Rank: {rank}, Score: {score}. {send_menu_msg}"
            try:
                player.socket.sendall(message.encode())
            except Exception as e:
                print(f"Failed to send to client: {e}")

def is_convertible_to_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
class game_message():
    def __init__(self,client_socket,message,roomid):
        self.socket = client_socket
        self.msg = message
        self.id  = roomid
class game_message_queue():
    def __init__(self):
        self.queue = []
        self.finised_queue = []
        self.leave_queue = []
    def add(self,msg,client_socket,rid):
        self.queue.append(game_message(client_socket,msg,rid))
        print("add mess to queue")
    def remove_msg(self,msga,client_socket,rid):
        for msge in self.queue:
            if msge.socket == client_socket:
                if msge.msg == msga:
                    if msge.id == rid:
                        self.queue.remove(msge)
    def add_finished_msg(self,roomid):
        self.finised_queue.append(roomid)
    def add_leave_queue(self,client_socket):
        self.leave_queue.append(client_socket)
    def remove_special_msg(self,roomid):
        for msge in self.finised_queue:
            if msge == roomid:
                self.finised_queue.remove(msge)
def game_room_handle(roomid,message_queue,sockfd_list):
    game = game_progess(sockfd_list)
    result = random.randint(1,100)
    print(result)
    countdown = 30
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        remaining = countdown - elapsed

        if remaining <= 0:
            print("Time's up!")
            break
        for msge in message_queue.queue:
            if msge.id == roomid:
                if is_convertible_to_int(msge.msg) == False:
                    msge.socket.sendall(b"your result is not valid, pls go with an interger")
                    message_queue.remove_msg(msge.msg,msge.socket,roomid)
                    continue
                data = int(msge.msg)
                if data < result:
                    msge.socket.sendall(b"your guess is smaller than the final result")
                    game.incre(msge.socket)
                    message_queue.remove_msg(msge.msg,msge.socket,roomid)
                if data > result:
                    msge.socket.sendall(b"your guess is bigger than the final result")
                    game.incre(msge.socket)
                    message_queue.remove_msg(msge.msg,msge.socket,roomid)
                if data == result:
                    msge.socket.sendall(b"you guess is right !!!!")
                    game.incre(msge.socket)
                    game.time(msge.socket,countdown-remaining)
                    message_queue.remove_msg(msge.msg,msge.socket,roomid)
    game.time_up()
    game.announce_results()
    message_queue.add_finished_msg(roomid)
#useless


class player():
    def __init__(self,client_socket,addr):
        self.sock = client_socket
        self.address = addr
        self.in_game = False
        self.in_room = False
        self.in_ready = False # ready to start
        self.host = False
        self.room_id = ""
        self.name = "" # player name
    def out(self):
        print(f"{self.address}: room id {self.room_id} {self.in_room}")
class player_list():
    def __init__(self):
        self.list = []
        self.size = 0
    def add(self,user):
        self.list.append(user)
# add function
    def get_player(self, client_socket):
        for client in self.list:
            if client.sock == client_socket:
                return client
                break

    def leave_room(self,client_socket):
        for client in self.list:
            if client.sock == client_socket:
                client.in_room = False
                client.in_game = False
                print("a player just leave the room")
                client.room_id = ""
    def roomdisban(self,roomid):
        for client in self.list:
            if client.room_id == roomid:
                client.in_room = False
                client.in_game = False
                client.roomid = ""
    def finised_game(self,rid):
        for player in self.list :
            if player.room_id == rid:
                player.in_game = False
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
                    return 1 # not in room
                else:
                    return -1
    def join_room(self,client_socket,roomid):
        for clients in self.list:
            if clients.sock == client_socket:
                clients.room_id = roomid
                clients.in_room = True
                
    def check_host(self,client_socket):
        for clients in self.list:
            if clients.sock == client_socket:
                if clients.host == True:
                    return clients.room_id
                else:
                    return -1
                
    def get_room_id(self, client_socket):
        for client in self.list:
            if client.sock == client_socket:
                return client.room_id
        return None

    def start_game(self,id):
        for clients in self.list:
            if clients.room_id == id :
                clients.in_game = True
                print(f"Player {clients.address} is now in game.")
    def check_ingame(self,client_socket):
        for clients in self.list:
            if clients.sock == client_socket:
                if clients.in_game == True:
                    return 1
                else:
                    return -1
                
    def set_ready(self,client_socket):
        for clients in self.list:
            if clients.sock == client_socket:
                if clients.in_ready == False:
                    clients.in_ready = True
                    print(f"Player {clients.address} is now ready.")
                else:
                    clients.in_ready = False
                    print(f"Player {clients.address} is not ready.")
                break
# check all players in the room are ready    
    def check_all_ready(self, room_id):
        ready = True
        for clients in self.list:
            if clients.room_id == room_id and not clients.host:  # Exclude the host
                if not clients.in_ready:
                    ready = False
                    break
        return ready
    def print(self):
        for clients in self.list:
            clients.out()
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
    def game_start(self):
        self.state = 1
    def get_state(self):
        return self.state
    def done_game(self):
        self.state = -1

class room_list():
    def __init__(self):
        self.rlist = []
        self.length = 0
    def leaveroom(self,rid,client_socket):
        for room in self.rlist:
            if room.id == rid:
                room.roomleave(client_socket)  
    def add(self,room):
        self.rlist.append(room)
    def addguest(self,guest_socket,room_id):
        for room in self.rlist:
            if room.id == room_id:
                room.addplayer(guest_socket)
    def socklist(self,room_id):
        for room in self.rlist:
            if room.id == room_id:
                temp = room.fdlist()
                return temp
    def disband(self,room_id):
        for room in self.rlist:
            if room.id == room_id:
                self.rlist.remove(room)
    def start_game(self,room_id):
        for room in self.rlist:
            if room.id == room_id:
                room.game_start()
    def check_state(self,room_id):
        for room in self.rlist:
            if room.id == room_id:
                return room.get_state()
    def game_done(self,room_id):
        for room in self.rlist:
            if room.id == room_id:
                room.done_game()
                break
# Create server socket
player_list= player_list()
room_list= room_list()
ur = UniqueRandom(0, 10)
msg_queue = game_message_queue()
threading.Thread(target=finished_game,args= (player_list,room_list,msg_queue,)).start()
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

            # Ask for username
            client_socket.sendall(b"Please enter your username: ")

        else:
            try:
                data = notified_socket.recv(1024)
                if data:
                    # handle username
                    existing_player = player_list.get_player(notified_socket)
                    if existing_player is None:
                        # First message is the username
                        username = data.decode().strip()
                        if username in ["1", "2", "3", "x"] or username == "":
                            msg = "Invalid username. Please enter a valid username: "
                            notified_socket.sendall(msg.encode())
                            continue

                        new_player = player(notified_socket, clients[notified_socket])
                        new_player.name = username
                        player_list.add(new_player)
                        print(f"Username '{username}' registered for {clients[notified_socket]}")
                        menu = send_menu(notified_socket, player_list)
                        welcome_msg = f"Welcome {username}! {menu}"
                        notified_socket.sendall(welcome_msg.encode())
                        continue
                    print(f"Received from {clients[notified_socket]}: {data.decode().strip()}")
                    
                    #handle data from game
                    if player_list.check_ingame(notified_socket) == 1:
                        roomid = player_list.get_room_id(notified_socket)
                        print(f"request check room id {roomid}")
                        if roomid is not None:
                            msg_queue.add(data, notified_socket, roomid)
                            continue # block futher process
  
                    # Room menu options
                    if player_list.check_join_room(notified_socket) == -1:
                        # option 1: start game
                        if data.decode().strip() == "1":
                            room_id = player_list.check_host(notified_socket)
                            if room_id == -1:
                                # Guest marking as ready                                
                                player_list.set_ready(notified_socket)
                                if player_list.get_player(notified_socket).in_ready == True:
                                    msg = "You are now ready! Waiting for host to start the game."
                                    send_menu_msg = send_menu(notified_socket, player_list)
                                    msg = f"{msg} {send_menu_msg}"
                                    notified_socket.sendall(msg.encode())
                                else:
                                    msg = "You are now not ready!"
                                    send_menu_msg = send_menu(notified_socket, player_list)
                                    msg = f"{msg} {send_menu_msg}"
                                    notified_socket.sendall(msg.encode())
                                
                                notified_socket.sendall(msg.encode())
                            else:
                                # Host starting game
                                if player_list.check_all_ready(room_id):
                                    msg = "Game is starting!"
                                    for sock in room_list.socklist(room_id):
                                        try:
                                            sock.sendall(msg.encode())
                                        except:
                                            continue
                                    event_finished_game.clear() #useless 
                                    room_list.start_game(roomid)
                                    player_list.start_game(room_id)
                                    threading.Thread(target=game_room_handle, args=(room_id, msg_queue, room_list.socklist(room_id))).start()
                                else:
                                    send_menu_msg = send_menu(notified_socket, player_list)
                                    msg = f"Not all players are ready! {send_menu_msg}"
                                    notified_socket.sendall(msg.encode())
             
                        # Option 2: Chat
                        elif data.decode().strip() == "2":
                            msg = "Enter your message: "
                            notified_socket.sendall(msg.encode())
                            try:
                                # Use select to ensure the socket is ready to read
                                readable, _, _ = select.select([notified_socket], [], [], 5)
                                if notified_socket in readable:
                                    chat_data = notified_socket.recv(1024).decode().strip()
                                    if chat_data:
                                        room_id = player_list.get_room_id(notified_socket)
                                        
                                        for sock in room_list.socklist(room_id):
                                            if sock != notified_socket:
                                                sock.sendall(f"{player_list.get_player(notified_socket).name}: {chat_data}".encode())
                                        send_menu_msg = send_menu(notified_socket, player_list)
                                        msg = f"Message sent! {send_menu_msg}"
                                        notified_socket.sendall(msg.encode())
                                    else:
                                        send_menu_msg = send_menu(notified_socket, player_list)
                                        msg = f"Empty message. {send_menu_msg}"
                                        notified_socket.sendall(msg.encode())
                                else:
                                    # No response from the client within the timeout
                                    send_menu_msg = send_menu(notified_socket, player_list)
                                    msg = f"No response received. {send_menu_msg}"
                                    notified_socket.sendall(msg.encode())
                                    
                            except Exception as e:
                                print(f"Error while processing chat: {e}")
                                send_menu_msg = send_menu(notified_socket, player_list)
                                msg = f"An error occurred. Please try again! {send_menu_msg}"
                                notified_socket.sendall(msg.encode())
                        # option x: leave game + disban          
                        elif (data.decode().strip() == "x"):
                            roomid = player_list.check_host(notified_socket)

                            if roomid == -1:
                                roomid = player_list.get_room_id(notified_socket)
                                player_list.leave_room(notified_socket)
                                room_list.leaveroom(roomid,notified_socket)
                                send_menu_msg = send_menu(notified_socket, player_list)
                                msg = f"you leave the room {send_menu_msg}"
                                notified_socket.sendall(msg.encode())
                                continue

                            else:
                                roomid = player_list.get_room_id(notified_socket)
                                player_list.leave_room(notified_socket)
                                room_list.disband(roomid)
                                player_list.roomdisban(roomid)
                                send_menu_msg = send_menu(notified_socket, player_list)
                                msg = f"room disbanded! {send_menu_msg}"
                                notified_socket.sendall(msg.encode())
                                continue
                        # option wrong
                        else:
                            send_menu_msg = send_menu(notified_socket, player_list)
                            msg = f"Unknown command. {send_menu_msg}"
                            notified_socket.sendall(msg.encode())

                    # Home menu options
                    else:
                        # option 1: create room
                        if (data.decode().strip() == "1"):
                                # set host status
                                temp = player_list.check_create_room(notified_socket)

                                if temp == 1:
                                    roomid = ur.get()
                                    room_list.add(game_room(notified_socket,roomid))
                                    player_list.join_room(notified_socket,roomid)
                                    send_menu_msg = send_menu(notified_socket, player_list)
                                    msg = f"Room {roomid} created! {send_menu_msg}"
                                    notified_socket.sendall(msg.encode())

 
                        # Option 2: Join room, check if game is in progress
                        elif data.decode().strip() == "2":  
                            notified_socket.sendall(b"Enter the room number: ")
                            try:
                                # Use select to ensure the socket is ready to read
                                readable, _, _ = select.select([notified_socket], [], [], 5)
                                if notified_socket in readable:
                                    room_data = notified_socket.recv(1024).decode().strip()
                                    if room_data.isdigit():
                                        room_id = int(room_data)
                                        # Check if the room exists
                                        if any(room.id == room_id for room in room_list.rlist):
                                            if room_list.check_state(room_id) == 1:
                                                notified_socket.sendall(b"[Room] The game is in progress")
                                                continue
                                            # Add the player to the room
                                            room_list.addguest(notified_socket, room_id)
                                            player_list.join_room(notified_socket, room_id)
                                            send_menu_msg = send_menu(notified_socket, player_list)
                                            msg = f"Joined room {room_id}! {send_menu_msg}"
                                            notified_socket.sendall(msg.encode())
                                        else:
                                            # Room does not exist
                                            send_menu_msg = send_menu(notified_socket, player_list)
                                            msg = f"Room {room_id} does not exist! {send_menu_msg}"
                                            notified_socket.sendall(msg.encode())
                                    else:
                                        # Invalid input (not a number)
                                        send_menu_msg = send_menu(notified_socket, player_list)
                                        msg = f"Invalid input. Please enter a valid room number! {send_menu_msg}"
                                        notified_socket.sendall(msg.encode())
                                else:
                                    # No response from the client within the timeout
                                    send_menu_msg = send_menu(notified_socket, player_list)
                                    msg = f"No response received. {send_menu_msg}"
                                    notified_socket.sendall(msg.encode())
                            except Exception as e:
                                print(f"Error while processing room join: {e}")
                                send_menu_msg = send_menu(notified_socket, player_list)
                                msg = f"An error occurred. Please try again! {send_menu_msg}"
                                notified_socket.sendall(msg.encode())
                                
                        # Option 3: List rooms
                        elif (data.decode().strip() == "3"):  
                            if len(room_list.rlist) == 0:
                                msg = "No rooms available."
                            else:
                                msg = "Available rooms: \n"
                                for room in room_list.rlist:
                                    msg += f"Room ID: {room.id}, Number of player: {len(room.guest_sock) + 1}\n"
                            send_menu_msg = send_menu(notified_socket, player_list)
                            msg = f"{msg} {send_menu_msg}"
                            notified_socket.sendall(msg.encode())

                        # Option x: Leave game
                        elif (data.decode().strip() == "x"):  
                            msg = "Are you sure you want to leave the game? (y/n): "
                            notified_socket.sendall(msg.encode())  
                            # Wait for confirmation
                            readable, _, _ = select.select([notified_socket], [], [], 5)
                            if notified_socket in readable:
                                confirmation = notified_socket.recv(1024).decode().strip()
                                if confirmation.lower() == 'y':
                                    msg = "Goodbye."
                                    notified_socket.sendall(msg.encode())

                                else:
                                    send_menu_msg = send_menu(notified_socket, player_list)
                                    msg = f"You chose to stay in the game. {send_menu_msg}"
                                    notified_socket.sendall(msg.encode())
                            else:
                                # No response from the client within the timeout
                                send_menu_msg = send_menu(notified_socket, player_list)
                                msg = f"Timeout. You are still in the game. {send_menu_msg}"
                                notified_socket.sendall(msg.encode())
                        # option wrong
                        else:
                            send_menu_msg = send_menu(notified_socket, player_list)
                            msg = f"Unknown command. {send_menu_msg}"
                            notified_socket.sendall(msg.encode())
                    
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
