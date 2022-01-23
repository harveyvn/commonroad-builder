from shapely.geometry import LineString, Point


class Lane:
    def __init__(self, left_boundary: LineString, right_boundary: LineString):
        self.left_boundary = left_boundary
        self.right_boundary = right_boundary

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)