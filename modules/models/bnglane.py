from typing import List, Tuple


class Stripe:
    def __init__(self, points: List, num: str, pattern: str):
        self.points = points
        self.num = num
        self.pattern = pattern

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)


class BngLane:
    def __init__(self, left: Stripe, right: Stripe, mid: List[Tuple], width: float):
        self.left = left
        self.right = right
        self.mid = mid
        self.width = width

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
