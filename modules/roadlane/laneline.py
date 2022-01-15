from shapely.geometry import LineString, Point


class Laneline:
    def __init__(self, coords: list, width: float, lane_id: int = 0):
        self.id = lane_id
        self.coords = coords
        self.width = width

    def get_linestring(self):
        return LineString([Point(p[0], p[1]) for p in self.coords])

    def get_line(self):
        return [self.coords[0], self.coords[-1]]

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)