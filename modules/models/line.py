from modules.constant import CONST


class Line:
    def __init__(self, marks: dict):
        total = sum(v.pattern for v in marks.values())
        self.num = CONST.SINGLE if len(marks.keys()) < 3 else CONST.DOUBLE
        self.pattern = CONST.SOLID if total / len(marks.keys()) > 2 / 3 else CONST.DASHED

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
