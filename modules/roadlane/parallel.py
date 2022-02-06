from .creator import RoadLane
from .laneline import Laneline
from shapely.geometry import LineString, Point
from modules.constant import CONST
from modules.models import Segment
from modules.common import find_boundaries, order_points, orient, interpolate


class ParallelLane(RoadLane):
    def process(self):
        coords = order_points(self.params["roads"][0])
        image = self.params["image"]

        is_horizontal, is_vertical = orient(coords)
        distance = Point(coords[-1]).distance(Point(coords[0]))
        axis_idx = 0 if is_vertical else 1
        target = (image.shape[axis_idx] * 0.6) if is_vertical else (image.shape[axis_idx] * 0.6)
        if distance < target:
            coords = interpolate(coords, axis_idx, image)

        baseline = Laneline(lane_id=0, coords=coords, width=0)
        lefts, rights = find_boundaries(image, baseline.get_line())

        segment = Segment(road_id=baseline.id,
                          left_boundary=LineString(lefts),
                          right_boundary=LineString(rights),
                          mid_line=baseline.get_linestring(),
                          kind=CONST.ROAD_PARALLEL)

        segment.is_horizontal = is_horizontal
        segment.is_vertical = is_vertical

        return self.params["image"], [baseline], [segment]
