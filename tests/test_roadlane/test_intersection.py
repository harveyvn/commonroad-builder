import unittest
from modules.crisce import extract_data_from_scenario
from modules.roadlane import categorize_roadlane


class TestIntersection(unittest.TestCase):
    def test_extract_three_roads_from_case02(self):
        data = extract_data_from_scenario("../cases/02")
        roadlane_factory = categorize_roadlane(data)
        (image, baselines, roads) = roadlane_factory.run()
        self.assertEqual(len(baselines), 3)
        self.assertEqual(len(roads), 3)

    def test_extract_four_roads_from_case03(self):
        data = extract_data_from_scenario("../cases/03")
        roadlane_factory = categorize_roadlane(data)
        (image, baselines, roads) = roadlane_factory.run()
        self.assertEqual(len(baselines), 4)
        self.assertEqual(len(roads), 4)

    def test_extract_four_roads_from_case04(self):
        data = extract_data_from_scenario("../cases/04")
        roadlane_factory = categorize_roadlane(data)
        (image, baselines, roads) = roadlane_factory.run()
        self.assertEqual(len(baselines), 4)
        self.assertEqual(len(roads), 4)

    def test_extract_two_roads_from_case05(self):
        data = extract_data_from_scenario("../cases/05")
        roadlane_factory = categorize_roadlane(data)
        (image, baselines, roads) = roadlane_factory.run()
        self.assertEqual(len(baselines), 2)
        self.assertEqual(len(roads), 2)

    def test_extract_four_roads_from_case06(self):
        data = extract_data_from_scenario("../cases/06")
        roadlane_factory = categorize_roadlane(data)
        (image, baselines, roads) = roadlane_factory.run()
        self.assertEqual(len(baselines), 4)
        self.assertEqual(len(roads), 4)


if __name__ == '__main__':
    unittest.main()
