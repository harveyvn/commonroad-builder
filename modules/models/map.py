from .road import Road
import matplotlib.pyplot as plt


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

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
