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
        self.state = -1  # -1: not ready, 0: ready, 1: game in progress

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


def finished_game(player_list, room_list, msg_queue):
    while True:
        for msg in msg_queue.finised_queue:
            player_list.finised_game(msg)


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
    countdown = 30  # Updated countdown value from server2.py
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

    game.time_up()
    game.announce_results()
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
            print(f"[Log] Accepted new connection from {client_address}")
            player_list.add(player(client_socket, client_address))

        else:
            try:
                data = notified_socket.recv(1024)
                if data:
                    print(f"[Log] Received from {clients[notified_socket]}: {data.decode().strip()}")
                    if player_list.check_ingame(notified_socket) == 1:
                        roomid = player_list.get_room_id(notified_socket)
                        print(f"[Log] Request from room ID {roomid}")
                        if roomid is not None:
                            msg_queue.add(data, notified_socket, roomid)
                        continue

                    if data.decode().strip() == "/leave":
                        if player_list.check_join_room(notified_socket) == -1:
                            roomid = player_list.get_room_id(notified_socket)
                            player_list.leave_room(notified_socket)
                            room_list.leaveroom(roomid, notified_socket)
                        else:
                            notified_socket.sendall(b"[Game] You are not in a room")

                    if data.decode().strip() == "/disband":
                        roomid = player_list.check_host(notified_socket)
                        if roomid == -1:
                            notified_socket.sendall(b"[Game] You are not the host.")
                        else:
                            player_list.roomdisban(roomid)

                    if data.decode().strip() == "/create":
                        temp = player_list.check_create_room(notified_socket)
                        if temp == 1:
                            roomid = ur.get()
                            room_list.add(game_room(notified_socket, roomid))
                            player_list.join_room(notified_socket, roomid)
                            msg = f"[Room] Room created with ID [{roomid}]"
                            notified_socket.sendall(msg.encode())
                        elif temp == -1:
                            notified_socket.sendall(b"[Game] You are in a game room")

                    if data.decode().strip() == "/start":
                        notified_socket.sendall(b"[Room] The Host started the game")
                        roomid = player_list.check_host(notified_socket)
                        if roomid == -1:
                            notified_socket.sendall(b"You are not the Host")
                        else:
                            room_list.start_game(roomid)
                            player_list.start_game(roomid)
                            temp = room_list.socklist(roomid)
                            player_list.print()
                            threading.Thread(target=game_room_handle, args=(roomid, msg_queue, temp)).start()

                    parts = data.decode().strip().split()
                    if parts[0] == "/join":
                        print(f"[Log] A client joined {parts[1]}")

                        if player_list.check_join_room(notified_socket) == 1:
                            if room_list.check_state(int(parts[1])) == 1:
                                notified_socket.sendall(b"[Room] The game is in progress")
                                continue
                            room_id = int(parts[1])
                            print(f"{room_id}")
                            room_list.addguest(notified_socket, room_id)
                            player_list.join_room(notified_socket, room_id)
                            notified_socket.sendall(b"[Room] Joined successfully")
                        else:
                            notified_socket.sendall(b"[Room] You are in a room")

                else:
                    # No data — client disconnected
                    print(f"[Log] Closed connection from {clients[notified_socket]}")
                    sockets_list.remove(notified_socket)
                    del clients[notified_socket]
                    notified_socket.close()
            except ConnectionResetError:
                print(f"[Log] Connection reset by {clients[notified_socket]}")
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                notified_socket.close()

    for err_socket in exception_sockets:
        sockets_list.remove(err_socket)
        err_socket.close()
        del clients[err_socket]
