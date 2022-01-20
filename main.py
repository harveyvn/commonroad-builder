from modules.crisce import extract_data_from_scenario
from modules.roadlane import categorize_roadlane
from modules.analyzer import Analyzer
from modules.models import Map


if __name__ == '__main__':
    road_data = extract_data_from_scenario("cases/06")
    lane_factory = categorize_roadlane(road_data)
    (image, baselines, roads) = lane_factory.run()

    for road in roads:
        analyzer = Analyzer(image=image, lanelines=baselines, road=road)
        lane_dict = analyzer.search_laneline()
        analyzer.categorize_laneline(lane_dict)

    network = Map(roads, image)
    network.draw(include_image=True)


