from .road import Road
import matplotlib.pyplot as plt


class Map:
    def __init__(self, roads: [Road], image):
        self.width = image.shape[1]
        self.height = image.shape[0]
        self.roads = roads
        self.image = image

    def draw(self, include_image: bool = False):
        if include_image:
            plt.imshow(self.image, cmap="gray")
        plt.title("Map")
        for road in self.roads:
            left_boundary = road.left_boundary
            plt.plot([p[0] for p in list(left_boundary.coords)],
                     [p[1] for p in list(left_boundary.coords)],
                     color="blue")
            for lane in road.lane_markings[1:-1]:
                mid_lanes = []
                color = "tomato"
                if lane.type == 1:
                    mid_lanes.append(left_boundary.parallel_offset(distance=lane.ratio * road.width,
                                                                   side="right", join_style=2))
                elif lane.type == 3:
                    mid_lanes.append(left_boundary.parallel_offset(distance=lane.ratio * road.width - 1.5,
                                                                   side="right", join_style=2))
                    mid_lanes.append(left_boundary.parallel_offset(distance=lane.ratio * road.width + 1.5,
                                                                   side="right", join_style=2))
                    color = "red"
                for mid_lane in mid_lanes:
                    plt.plot([p[0] for p in list(mid_lane.coords)],
                             [p[1] for p in list(mid_lane.coords)],
                             color=color,
                             linestyle="dashed")

            right_boundary = road.right_boundary
            plt.plot([p[0] for p in list(right_boundary.coords)],
                     [p[1] for p in list(right_boundary.coords)],
                     color="green")
        plt.gca().set_aspect("equal")
        plt.show()

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
