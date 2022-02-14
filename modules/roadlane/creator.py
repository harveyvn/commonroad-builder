from __future__ import annotations
from abc import ABC, abstractmethod
from modules.constant import CONST
from modules.common import pairs, angle, reverse_geom
from shapely.geometry import LineString


class RoadwayCreator(ABC):
    """
    The RoadwayCreator class declares the factory method that returns a new RoadLane object.
    The return type of this method must match the RoadLane interface.
    """

    def __init__(self, params):
        self.params = params

    @abstractmethod
    def create(self) -> RoadLane:
        """
        Return the RoadLane with its appropriate type
        """
        pass

    def run(self):
        """
        Call the certain roadlane object and process analyzer
        """
        return self.create().process()


class RoadLane(ABC):
    """
    The RoadLane interface declares the operations that all concrete RoadLane
    must implement.
    """

    def __init__(self, params):
        self.params = params

    @abstractmethod
    def process(self):
        """
        Return
        """
        pass


"""
Concrete Creators override the factory method in order to 
generate a different type of mutator.
"""


class LinearCreator(RoadwayCreator):

    def create(self) -> RoadLane:
        from .linearity import LinearLane
        return LinearLane(self.params)


class IntersectionCreator(RoadwayCreator):

    def create(self) -> RoadLane:
        from .intersection import IntersectionLane
        return IntersectionLane(self.params)


class ParallelCreator(RoadwayCreator):

    def create(self) -> RoadLane:
        from .parallel import ParallelLane
        return ParallelLane(self.params)


def refine_roadlanes(roadway_data):
    i, lst_dicts = 0, list()
    for road in roadway_data["roads"]:
        lst_dicts.append({
            "i": i,
            "ls": LineString(road)
        })
        i += 1

    parallel_set = set()
    for lsd1, lsd2 in pairs(lst_dicts):
        if angle(lsd1["ls"].coords, lsd2["ls"].coords) > 175:
            lsd2["ls"] = reverse_geom(lsd2["ls"])
            parallel_set.add(lsd1["i"])
            parallel_set.add(lsd2["i"])
        if -5 < angle(lsd1["ls"].coords, lsd2["ls"].coords) < 5:
            parallel_set.add(lsd1["i"])
            parallel_set.add(lsd2["i"])

    parallel_lst = []
    for i in parallel_set:
        for ls_dict in lst_dicts:
            if ls_dict["i"] == i:
                parallel_lst.append(ls_dict["ls"])

    if len(parallel_lst) == len(lst_dicts):
        roadway_data["road_type"] = CONST.ROAD_PARALLEL
        roadway_data["roads"] = [list(parallel_lst[0].coords)]
        roadway_data["lane_widths"] = [0]
        roadway_data["lengths"] = [roadway_data["lengths"][0]]
        return roadway_data

    return roadway_data


def categorize_roadlane(roadway_data: dict) -> RoadwayCreator:
    """
    Return a specific lane analyzer up to the roadway type
    """
    if roadway_data["road_type"] == CONST.ROAD_CURVE_OR_STRAIGHT:
        return LinearCreator(roadway_data)
    if roadway_data["road_type"] == CONST.ROAD_INTERSECTION:
        return IntersectionCreator(roadway_data)
    if roadway_data["road_type"] == CONST.ROAD_PARALLEL:
        return ParallelCreator(roadway_data)

    raise Exception("Exception: RoadLane Type not found!")