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
    def get_state(self,room_id):
        for room in self.rlist:
            if room.id == room_id:
                return room.check_state()