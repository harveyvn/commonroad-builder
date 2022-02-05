from __future__ import annotations
from abc import ABC, abstractmethod
from modules.constant import CONST


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