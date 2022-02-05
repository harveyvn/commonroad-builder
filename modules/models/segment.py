from .lane_marking import LaneMarking
from .lane import Lane
from shapely.geometry import Polygon, LineString
from ..common import pairs, reverse_geom


class Segment:
    def __init__(self, kind, mid_line: LineString, width: float = 0, road_id: int = 0, reversed: bool = False,
                 left_boundary: LineString = None, right_boundary: LineString = None):
        self.id = road_id
        self.kind = kind
        self.left_boundary = left_boundary
        self.right_boundary = right_boundary
        self.mid_line = mid_line
        self.width = width
        self.poly = Polygon([*list(left_boundary.coords), *list(right_boundary.coords)])
        self.reversed = reversed
        self.lane_markings: [LaneMarking] = []
        self.lanes: [Lane] = []
        self.angle: float = 0
        self.is_horizontal = False
        self.is_vertical = False

    def generate_lanes(self):
        lines = []
        left_boundary = self.left_boundary
        lines.append(left_boundary)

        for mark in self.lane_markings[1:-1]:
            lines.append(left_boundary.parallel_offset(distance=-(mark.ratio * self.width), side="left", join_style=2))

        right_boundary = reverse_geom(self.right_boundary)
        lines.append(right_boundary)
        lanes = []
        for segment in pairs(lines):
            lanes.append(Lane(segment[0], segment[1]))
        self.lanes = lanes

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
