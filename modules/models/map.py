from .road import Road
import matplotlib.pyplot as plt
import json


class Map:
    def __init__(self, roads: [Road], image):
        self.width = image.shape[1]
        self.height = image.shape[0]
        self.roads = roads
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
                fig.savefig(f'{i}.png', bbox_inches="tight")
                i = i+1

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

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
