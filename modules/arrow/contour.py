from typing import Tuple


class Contour:
    def __init__(self, idx: int, length: float, centeroid: Tuple[int, int], coords):
        self.idx = idx
        self.length = length
        self.centeroid = centeroid
        self.coords = coords
        self.type = None
        self.vertexes = None

    def set_type(self, shape):
        self.type = shape

    def set_vertexes(self, vertexes):
        self.vertexes = vertexes

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
