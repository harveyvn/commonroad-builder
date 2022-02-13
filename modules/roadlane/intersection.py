from . import RoadLane
from .laneline import Laneline
from math import ceil
from modules.models import Segment
from modules.constant import CONST
from modules.common import order_points, orient


class IntersectionLane(RoadLane):

    def process(self):
        lane_widths = self.params["lane_widths"]
        image = self.params["image"]
        buffer = 0.00005

        baselines = []
        for i, coord in enumerate(self.params["roads"]):
            baselines.append(Laneline(lane_id=i, coords=order_points(coord), width=lane_widths[i] / 2))

        segments = []
        for idx, laneline in enumerate(baselines):
            mid = laneline.get_linestring()
            right = mid.parallel_offset(distance=ceil(laneline.width + buffer), side="right", join_style=2)
            left = mid.parallel_offset(distance=ceil(laneline.width + buffer), side="left", join_style=2)
            is_horizontal, is_vertical = orient(laneline.coords)
            sm = Segment(road_id=laneline.id, width=lane_widths[laneline.id],
                         mid_line=mid, left_boundary=left, right_boundary=right,
                         kind=CONST.ROAD_CURVE_OR_STRAIGHT)
            sm.is_horizontal = is_horizontal
            sm.is_vertical = is_vertical
            segments.append(sm)

        return image, baselines, segments
