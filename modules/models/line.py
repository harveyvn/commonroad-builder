from math import trunc
from shapely.geometry import LineString
from modules.constant import CONST


class Line:
    def __init__(self, marks: dict = None, ls: LineString = None, thickness: int = 4):
        if marks is not None:
            keys = list(marks.keys())
            threshold = 0.6 if len(keys) > 2 else 0.5
            total = sum(v.pattern for v in marks.values())

            if len(keys) < 4:
                self.num = CONST.SINGLE
            else:
                self.num = CONST.SINGLE if thickness / len(keys) > 1.5 else CONST.DOUBLE

            if total / len(keys) == 2:
                self.pattern = CONST.DOTTED
            elif total / len(keys) >= threshold:
                self.pattern = CONST.SOLID
            else:
                self.pattern = CONST.DASHED
            self.keys = keys
            # self.marks = marks
            # for m in marks:
            #     print(marks[m])
            # print([v.pattern for v in marks.values()])
            # print(total, len(keys))
            # print(total / len(keys), threshold, self.pattern)
            # print("======")
        self.ls = ls

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
