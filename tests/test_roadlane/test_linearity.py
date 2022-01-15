import unittest
from modules.crisce import extract_data_from_scenario
from modules.roadlane import categorize_roadlane


class TestLinearity(unittest.TestCase):
    def test_extract_straight_line_from_case_00(self):
        data = extract_data_from_scenario("../cases/00")
        roadlane_factory = categorize_roadlane(data)
        (image, baselines, roads) = roadlane_factory.run()
        self.assertEqual(len(baselines), 1)  # add assertion here
        self.assertEqual(len(roads), 1)  # add assertion here

    def test_extract_curved_line_from_case_01(self):
        data = extract_data_from_scenario("../cases/01")
        roadlane_factory = categorize_roadlane(data)
        (image, baselines, roads) = roadlane_factory.run()
        self.assertEqual(len(baselines), 1)  # add assertion here
        self.assertEqual(len(roads), 1)  # add assertion here


