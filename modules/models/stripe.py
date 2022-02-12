from typing import List


class Stripe:
    def __init__(self, points: List, num: int = -1, pattern: str = '-1'):
        self.points = points
        self.num = num
        self.pattern = pattern

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)