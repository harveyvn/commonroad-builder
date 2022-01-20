from .lane_marking import LaneMarking
from .lane import Lane
from shapely.geometry import Polygon, LineString


class Road:
    def __init__(self, left_boundary: LineString, right_boundary: LineString,
                 mid_line: LineString, width: float, road_id: int = 0, reversed: bool = False,
                 angle: float = 0):
        self.id = road_id
        self.left_boundary = left_boundary
        self.right_boundary = right_boundary
        self.mid_line = mid_line
        self.width = width
        self.poly = Polygon([*list(left_boundary.coords), *list(right_boundary.coords)])
        self.angle = angle
        self.reversed = reversed
        self.lane_markings: [LaneMarking] = []
        self.lanes: [Lane] = []

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
