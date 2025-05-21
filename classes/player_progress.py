class player_progress():
    def __init__(self,fd):
        self.socket = fd
        self.count = 0
        self.time = 30
        self.guessed_correct = False
        self.correct_time = None
    def increment(self):
        self.count = self.count + 1
    def add_time(self,time_finished):
        self.time = time_finished
        self.guess_in_time = 1
    def finished(self):
        self.socket.sendall(b"time up !!!")
    def point_cal(self):
        if self.guessed_correct:
            base = 100
            speed_bonus = max(0, int(100 - self.correct_time))
            guess_penalty = self.count * 5
            return max(10, base + speed_bonus - guess_penalty)
        else:
            return 0
