from . import RoadLane
from .laneline import Laneline
from math import ceil
from modules.models import Road


class ParallelLane(RoadLane):

    def process(self):
        print(self.params)
        exit()
        lane_widths = self.params["lane_widths"]
        lengths = self.params["lengths"]
        image = self.params["image"]

        baselines = []
        for i, coord in enumerate(self.params["roads"]):
            baselines.append(Laneline(lane_id=i, coords=coord, width=lane_widths[i] / 2))

        segments = []
        for idx, laneline in enumerate(baselines):
            mid_line = laneline.get_linestring()
            right_boundary = mid_line.parallel_offset(distance=ceil(laneline.width), side="left", join_style=2)
            left_boundary = mid_line.parallel_offset(distance=ceil(laneline.width), side="right", join_style=2)
            segments.append(Road(road_id=laneline.id,
                                 mid_line=mid_line,
                                 left_boundary=left_boundary,
                                 right_boundary=right_boundary,
                                 width=lane_widths[laneline.id]))

        return image, baselines, segments