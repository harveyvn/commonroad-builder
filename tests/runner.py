import unittest
import test_roadlane
import test_analyzer

if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    loader = unittest.TestLoader()
    suite = test_roadlane.load_tests(loader)
    suite = test_analyzer.load_tests(suite, loader)
    runner.run(suite)
