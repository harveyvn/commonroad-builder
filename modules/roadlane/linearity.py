from . import RoadLane
from .laneline import Laneline
from math import ceil
from modules.models import Segment
from modules.constant import CONST
from modules.common import order_points


class LinearLane(RoadLane):

    def process(self):
        lane_width = self.params["lane_width"]
        coords = self.params["coords"]
        image = self.params["image"]
        length = self.params["length"]

        # Define the polygon covering the road with the midline linestring, left & right boundaries
        buffer = 0.00005
        laneline = Laneline(coords=order_points(coords), width=lane_width / 2)
        mid_line = laneline.get_linestring()
        right_boundary = mid_line.parallel_offset(distance=ceil(laneline.width + buffer), side="right", join_style=2)
        left_boundary = mid_line.parallel_offset(distance=ceil(laneline.width + buffer), side="left", join_style=2)
        segment = Segment(mid_line=mid_line,
                          left_boundary=left_boundary,
                          right_boundary=right_boundary,
                          width=lane_width,
                          kind=CONST.ROAD_CURVE_OR_STRAIGHT)

        baselines, segments = [laneline], [segment]
        return image, baselines, segments
