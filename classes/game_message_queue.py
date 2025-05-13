from .game_message import game_message
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