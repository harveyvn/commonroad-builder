from . import RoadLane
from .laneline import Laneline
from .analyzer import Analyzer
from shapely import ops
from math import floor, ceil
from shapely.geometry import Polygon
from modules import angle


class IntersectionLane(RoadLane):

    def process(self):
        lane_widths = self.params["lane_widths"]
        lengths = self.params["lengths"]
        image = self.params["image"]

        roads = []
        for i, coord in enumerate(self.params["roads"]):
            roads.append(Laneline(i, coord, lane_widths[i] / 2))
        pairs = [(a.id, b.id) for idx, a in enumerate(roads) for b in roads[idx + 1:]]
        straight_pairs = []
        for pair in pairs:
            alpha = angle(roads[pair[0]].get_line(), roads[pair[1]].get_line())
            if 175 <= alpha <= 185:
                straight_pairs.append(pair)

        for pair in straight_pairs:
            polys = []
            for road in [roads[pair[0]], roads[pair[1]]]:
                baseline = road.get_linestring()
                left_boundary = baseline.parallel_offset(distance=ceil(road.width), side="left", join_style=2)
                right_boundary = baseline.parallel_offset(distance=ceil(road.width), side="right", join_style=2)
                poly = Polygon([*list(left_boundary.coords), *list(right_boundary.coords)])
                polys.append(poly)

            new_pol = ops.cascaded_union(polys)
            analyzer = Analyzer(new_pol, image, roads[pair[0]].coords, roads)
            analyzer.run()

        idx_used = set()
        for pair in straight_pairs:
            idx_used.add(pair[0])
            idx_used.add(pair[1])
        idx_used = list(sorted(idx_used))

        for idx, road in enumerate(roads):
            if idx in idx_used:
                continue
            baseline = road.get_linestring()
            left_boundary = baseline.parallel_offset(distance=ceil(road.width), side="left", join_style=2)
            right_boundary = baseline.parallel_offset(distance=ceil(road.width), side="right", join_style=2)
            poly = Polygon([*list(left_boundary.coords), *list(right_boundary.coords)])
            analyzer = Analyzer(poly, image, road.coords, roads)
            analyzer.run()

        return True
