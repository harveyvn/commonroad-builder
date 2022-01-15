from .road import Road


class Map:
    def __init__(self, width: int, height: int, roads: [Road]):
        self.width = width
        self.height = height
        self.roads = roads

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
