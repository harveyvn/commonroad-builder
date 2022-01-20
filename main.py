from modules.crisce import extract_data_from_scenario
from modules.roadlane import categorize_roadlane
from modules.analyzer import Analyzer
from modules.models import Map
import json

if __name__ == '__main__':
    road_data = extract_data_from_scenario("cases/01")
    lane_factory = categorize_roadlane(road_data)
    (image, baselines, roads) = lane_factory.run()

    for road in roads:
        analyzer = Analyzer(image=image, lanelines=baselines, road=road)
        lane_dict = analyzer.search_laneline()
        analyzer.categorize_laneline(lane_dict)
        road.generate_lanes()

    network = Map(roads, image)
    # network.draw(include_image=True)
    # convert to JSON string

    road_data = []
    for i, road in enumerate(roads):
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
