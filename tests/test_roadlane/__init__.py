import unittest
from .test_linearity import TestLinearity
from .test_intersection import TestIntersection


def load_tests(loader):
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestLinearity))
    suite.addTests(loader.loadTestsFromTestCase(TestIntersection))

    return suite
