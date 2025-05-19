class player_list():
    def __init__(self):
        self.list = []
        self.size = 0
    def add(self,user):
        self.list.append(user)
    def leave_room(self,client_socket):
        for client in self.list:
            if client.sock == client_socket:
                client.in_room = False
                client.in_game = False
                print("a player just leave the room")
                client.room_id = ""
                client.host = False
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
                    return 1
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
    def get_player(self, client_socket):
        for client in self.list:
            if client.sock == client_socket:
                return client
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
