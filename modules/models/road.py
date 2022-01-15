from .lane import Lane
from shapely.geometry import Polygon, LineString


class Road:
    def __init__(self, left_boundary: LineString, right_boundary: LineString,
                 mid_line: LineString, road_id: int = 0, angle: float = 0):
        self.id = road_id
        self.left_boundary = left_boundary
        self.right_boundary = right_boundary
        self.mid_line = mid_line
        self.poly = Polygon([*list(left_boundary.coords), *list(right_boundary.coords)])
        self.angle = angle
        self.lanes: [Lane] = []

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
