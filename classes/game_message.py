class game_message():
    def __init__(self,client_socket,message,roomid):
        self.socket = client_socket
        self.msg = message
        self.id  = roomid