class player():
    def __init__(self,client_socket,addr):
        self.sock = client_socket
        self.address = addr
        self.in_game = False
        self.in_room = False
        self.host = False
        self.room_id = ""
    def out(self):
        print(f"{self.address}: room id {self.room_id} {self.in_room}")