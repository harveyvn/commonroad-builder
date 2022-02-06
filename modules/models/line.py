from math import trunc
from modules.constant import CONST


class Line:
    def __init__(self, marks: dict):
        total = sum(v.pattern for v in marks.values())
        self.num = CONST.SINGLE if len(marks.keys()) < 4 else CONST.DOUBLE
        self.pattern = CONST.SOLID if total / len(marks.keys()) >= 2 / 3 else CONST.DASHED
        self.keys = list(marks.keys())
        self.ls = None

    def get_peak(self):
        length = len(self.keys)
        return self.keys[trunc(length / 2)]

    def set_ls(self, ls):
        self.ls = ls

    def get_first(self):
        first, last = self.ls.boundary
        return first

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
