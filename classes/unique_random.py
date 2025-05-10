import random
class UniqueRandom:
    def __init__(self, start, end):
        self.pool = list(range(start, end))
        random.shuffle(self.pool)

    def get(self):
        if not self.pool:
            raise ValueError("No more unique numbers left!")
        return self.pool.pop()