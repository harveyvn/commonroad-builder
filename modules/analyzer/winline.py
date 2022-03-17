from typing import List, Tuple
from modules.constant import CONST


class Winline:
    def __init__(self, points: List[Tuple], id: int = 0,
                 total: int = CONST.INVALID_LINE, zero_perc: float = CONST.INVALID_LINE):
        self.id = id
        self.points = points
        self.pattern = None

        if total > CONST.INVALID_LINE:
            if 0.4 <= zero_perc <= 0.6:
                self.pattern = CONST.DOTTED_INT
            elif zero_perc <= CONST.MAX_PERCENTAGE_ZEROS_CONT:
                self.pattern = CONST.SOLID_INT
            else:
                self.pattern = CONST.DASHED_INT

        self.total = total
        self.zero_perc = zero_perc

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
