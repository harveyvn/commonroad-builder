from modules.constant import CONST


class LaneMarking:
    def __init__(self, ratio, width):
        self.ratio = ratio
        self.width = width
        self.type = CONST.SINGLE_LINE

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
