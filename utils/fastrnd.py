from time import time


class FastRnd(object):
    
    R = 4.0

    def __init__(self, transform=lambda x: x, seed=None):
        while not seed or 0 < seed >=1:
            seed = time() % 1
        self.seed = seed
        self.transform = transform

    def __call__(self):
        self.seed = self.R * self.seed * (1.0 - self.seed)
        return self.transform(self.seed)

