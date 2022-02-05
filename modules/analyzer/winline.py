from typing import List, Tuple
from modules.constant import CONST


class Winline:
    def __init__(self, points: List[Tuple], id: int = 0,
                 total: int = CONST.INVALID_LINE, zero_perc: float = CONST.INVALID_LINE):
        self.id = id
        self.points = points
        self.pattern = None

        if zero_perc > CONST.MAX_PERCENTAGE_ZEROS_CONT and total > CONST.INVALID_LINE:
            self.pattern = CONST.DASHED_LINE
        else:
            self.pattern = CONST.CONT_LINE

        self.total = total
        self.zero_perc = zero_perc
