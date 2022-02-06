from typing import List, Tuple
from modules.constant import CONST


class Winline:
    def __init__(self, id: int = 0, total: int = CONST.INVALID_LINE, zero_perc: float = CONST.INVALID_LINE):
        self.id = id
        self.pattern = None

        if zero_perc > CONST.MAX_PERCENTAGE_ZEROS_CONT and total > CONST.INVALID_LINE:
            self.pattern = CONST.DASHED_INT
        else:
            self.pattern = CONST.SOLID_INT

        self.total = total
        self.zero_perc = zero_perc

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
