from typing import List

from .segment import Segment
from .lane_marking import LaneMarking
from .lane import Lane
import matplotlib.pyplot as plt
import json
from math import floor
from shapely.geometry import LineString
from modules.common import pairs


class Map:
    def __init__(self, segments: [Segment], image):
        self.width = image.shape[1]
        self.height = image.shape[0]
        self.roads = segments
        self.image = image

    def draw(self, include_image: bool = False):
        i = 1
        for road in self.roads:
            for lane in road.lanes:
                fig = plt.gcf()
                plt.title("Map")
                plt.imshow(self.image, cmap="gray")
                plt.plot([p[0] for p in list(lane.left_boundary.coords)],
                         [p[1] for p in list(lane.left_boundary.coords)],
                         color="blue")
                plt.plot([p[0] for p in list(lane.right_boundary.coords)],
                         [p[1] for p in list(lane.right_boundary.coords)],
                         color="green")
                plt.show()
                # fig.savefig(f'{i}.png', bbox_inches="tight")
                i = i + 1

    def write_to_json(self):
        road_data = []
        for i, road in enumerate(self.roads):
            lane_data = []
            for lane in road.lanes:
                lane_data.append({
                    "left_boundary": list(lane.left_boundary.coords),
                    "right_boundary": list(lane.right_boundary.coords)
                })
            road_data.append({
                "id": i,
                "width": road.width,
                "lanes": lane_data
            })
        result = {
            "roads": road_data
        }

        with open('result.json', 'w') as fp:
            json.dump(result, fp)

    def generate_road_with_ratio(self, lane_nodes, name="result"):
        road_data = []

        for i, lane_node in enumerate(lane_nodes):
            mid_line: LineString = LineString([(point[0], point[1]) for point in lane_node])
            width = lane_node[0][-1]

            lines = []
            left_boundary = mid_line.parallel_offset(distance=floor(width / 2), side="left", join_style=2)
            lines.append(left_boundary)

            correspond_segment: Road = self.roads[i]
            markings: List[LaneMarking] = correspond_segment.lane_markings
            for marking in markings[1:]:
                ratio = marking.ratio
                laneline: LineString = left_boundary.parallel_offset(distance=floor(width * ratio), side="right",
                                                                     join_style=2)
                laneline_list = list(laneline.coords).copy()
                laneline_list.reverse()
                lines.append(LineString(laneline_list))

            lanes = []
            for seg in pairs(lines):
                lanes.append(Lane(seg[0], seg[1]))

            lane_data = []
            for lane in lanes:
                lane_data.append({
                    "left_boundary": list(lane.left_boundary.coords),
                    "right_boundary": list(lane.right_boundary.coords)
                })

            road_data.append({"id": i, "width": width, "lanes": lane_data, "mid_line": list(mid_line.coords)})

        with open(f'{name}.json', 'w') as fp:
            json.dump({"roads": road_data}, fp)

        for road in road_data:
            for lane in road["lanes"]:
                left_boundary = lane["left_boundary"]
                right_boundary = lane["right_boundary"]
                plt.plot([p[0] for p in left_boundary],
                         [p[1] for p in left_boundary],
                         color="blue")
                plt.plot([p[0] for p in right_boundary],
                         [p[1] for p in right_boundary],
                         color="green")

        plt.gca().set_aspect('equal', 'box')
        plt.show()

        return road_data



    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
