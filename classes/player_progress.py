class player_progress():
    def __init__(self,fd):
        self.socket= fd
        self.count= 0
        self.time = 30
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
            base = 100
            speed_bonus = max(0, int(100 - self.time))
            guess_penalty = self.count * 5
            return max(0, base + speed_bonus - guess_penalty)
        else:
            return 0