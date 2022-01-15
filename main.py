from modules.crisce import extract_data_from_scenario
from modules.roadlane import categorize_roadlane
from modules.analyzer import Analyzer
from modules.models import Map
import matplotlib.pyplot as plt


if __name__ == '__main__':
    road_data = extract_data_from_scenario("cases/06")
    lane_factory = categorize_roadlane(road_data)
    (image, baselines, roads) = lane_factory.run()

    for road in roads:
        analyzer = Analyzer(image=image, lanelines=baselines, road=road)
        lane_dict = analyzer.search_laneline()
        analyzer.categorize_laneline(lane_dict)

    network = Map(image.shape[0], image.shape[1], roads)
    plt.imshow(image, cmap="gray")
    for road in roads:
        left_boundary = road.left_boundary
        plt.plot([p[0] for p in list(left_boundary.coords)],
                 [p[1] for p in list(left_boundary.coords)],
                 color="blue")
        for lane in road.lanes[1:-1]:
            mid_lanes = []
            color = "tomato"
            if lane.type == 1:
                mid_lanes.append(left_boundary.parallel_offset(distance=lane.ratio*road.width,
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

