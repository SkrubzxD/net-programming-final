import socket
import select
import random
import threading
import time

from classes.player import player
from classes.game_progress import game_progress
from classes.player_list import player_list
from classes.room_list import room_list
from classes.unique_random import UniqueRandom
from classes.game_message_queue import game_message_queue
from classes.send_menu import send_menu

HOST = '127.0.0.1'
PORT = 12344

event_finished_game = threading.Event()

class game_room():
    def __init__(self, host, iden):
        self.host_sock = host
        self.guest_sock = []
        self.capacity = 4
        self.id = iden
        self.state = -1  # -1: not ready, s1: game in progress

    def addplayer(self, player):
        self.guest_sock.append(player)

    def fdlist(self):
        return [self.host_sock] + self.guest_sock

    def roomleave(self, client_socket):
        if client_socket in self.guest_sock:
            self.guest_sock.remove(client_socket)
    def game_start(self):
        self.state = 1
    def get_state(self):
        return self.state
    def done_game(self):
        self.state = -1


def finished_game(player_list, room_list, msg_queue):
    while True:
        for msg in msg_queue.finised_queue:
            player_list.finised_game(msg)
            room_list.game_done(msg)
            msg_queue.remove_special_msg(msg)


def is_convertible_to_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def game_room_handle(roomid, message_queue, sockfd_list):
    game = game_progress(sockfd_list)
    result = random.randint(1, 100)
    print(result)
    countdown = 10  # Updated countdown value from server2.py
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        remaining = countdown - elapsed

        if remaining <= 0:
            print(f"[Log] Time's up for game in room ID [{roomid}]")
            game.time_up()
            game.announce_results()
            break

        for msge in message_queue.queue:
            if msge.id == roomid:
                if not is_convertible_to_int(msge.msg):
                    msge.socket.sendall(b"[Game] Invalid results, input a number.")
                    msge.socket.sendall(b"Your result is not valid, please enter an integer.")
                    message_queue.remove_msg(msge.msg, msge.socket, roomid)
                    continue
                data = int(msge.msg)
                if data < result:
                    msge.socket.sendall(b"[Game] Guess a larger number.")
                    msge.socket.sendall(b"Your guess is smaller than the final result.")
                    game.incre(msge.socket)
                    message_queue.remove_msg(msge.msg, msge.socket, roomid)
                elif data > result:
                    msge.socket.sendall(b"[Game] Guess a smaller number.")
                    msge.socket.sendall(b"Your guess is bigger than the final result.")
                    game.incre(msge.socket)
                    message_queue.remove_msg(msge.msg, msge.socket, roomid)
                else:
                    msge.socket.sendall(b"[Game] Correct!!!!")
                    msge.socket.sendall(b"Your guess is right!!!!")
                    game.incre(msge.socket)
                    game.time(msge.socket, countdown - remaining)
                    message_queue.remove_msg(msge.msg, msge.socket, roomid)


    message_queue.add_finished_msg(roomid)
    event_finished_game.set()


player_list = player_list()
room_list = room_list()
ur = UniqueRandom(0, 10)
msg_queue = game_message_queue()

threading.Thread(target=finished_game, args=(player_list, room_list, msg_queue)).start()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()
server_socket.setblocking(False)  # Make server socket non-blocking

# List of sockets to monitor for incoming data
sockets_list = [server_socket]
clients = {}

print(f"[Log] Server listening on {HOST}:{PORT}...")

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
                                    msg = "Game started!"
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
                                socklist = room_list.socklist(roomid)
                                player_list.leave_room(notified_socket)
                                room_list.disband(roomid)
                                player_list.roomdisban(roomid)
                                send_menu_msg = send_menu(notified_socket, player_list)
                                msg = f"Room {roomid} disbanded! {send_menu_msg}"                                
                                if socklist:
                                    for sock in socklist:
                                        sock.sendall(msg.encode())
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
                    # Remove from player_list and handle room logic
                    player = player_list.get_player(notified_socket)
                    if player:
                        roomid = player.room_id
                        is_host = player.host
                        player_list.leave_room(notified_socket)
                        if roomid:
                            if is_host:
                                # Host disconnected: disband room and notify others
                                
                                send_menu_msg = send_menu(notified_socket, player_list)
                                msg = f"Room {roomid} disbanded! {send_menu_msg}"
                                for sock in room_list.socklist(roomid):
                                    if sock != notified_socket:
                                        sock.sendall(msg.encode())
                                room_list.disband(roomid)
                                player_list.roomdisban(roomid)
                            else:
                                room_list.leaveroom(roomid, notified_socket)
                    
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
