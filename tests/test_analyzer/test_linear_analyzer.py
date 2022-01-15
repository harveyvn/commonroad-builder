import unittest
from modules.analyzer import Analyzer
from modules.crisce import extract_data_from_scenario
from modules.roadlane import categorize_roadlane


class TestLinearAnalyzer(unittest.TestCase):
    def test_extract_lanes_from_case_00(self):
        data = extract_data_from_scenario("../cases/00")
        roadlane_factory = categorize_roadlane(data)
        (image, baselines, roads) = roadlane_factory.run()
        for road in roads:
            analyzer = Analyzer(image=image, lanelines=baselines, road=road)
            lane_dict = analyzer.search_laneline()
            lanes = analyzer.categorize_laneline(lane_dict)
            road.lanes = lanes
            self.assertEqual(len(road.lanes), 3)

    def test_extract_lanes_from_case_01(self):
        data = extract_data_from_scenario("../cases/01")
        roadlane_factory = categorize_roadlane(data)
        (image, baselines, roads) = roadlane_factory.run()
        for road in roads:
            analyzer = Analyzer(image=image, lanelines=baselines, road=road)
            lane_dict = analyzer.search_laneline()
            lanes = analyzer.categorize_laneline(lane_dict)
            road.lanes = lanes
            self.assertEqual(len(road.lanes), 3)


if __name__ == '__main__':
    unittest.main()
