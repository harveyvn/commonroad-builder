from .creator import RoadLane
from .laneline import Laneline
from shapely.geometry import LineString
from modules.constant import CONST
from modules.models import Segment
from modules.common import find_left_right_boundaries, order_points


class ParallelLane(RoadLane):
    def process(self):
        baseline = Laneline(lane_id=0, coords=order_points(self.params["roads"][0]), width=0)
        lefts, rights, diff = find_left_right_boundaries(self.params["image"], baseline.get_line())

        segment = Segment(road_id=baseline.id,
                          left_boundary=LineString(lefts),
                          right_boundary=LineString(rights),
                          mid_line=baseline.get_linestring(),
                          kind=CONST.ROAD_PARALLEL)

        segment.is_horizontal = True if -2 <= diff <= 2 else False
        segment.is_vertical = True if 88 <= diff <= 92 else False

        return self.params["image"], [baseline], [segment]
