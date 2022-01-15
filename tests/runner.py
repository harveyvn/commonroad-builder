import unittest
import test_roadlane

if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    loader = unittest.TestLoader()
    suite = test_roadlane.load_tests(loader)
    runner.run(suite)
