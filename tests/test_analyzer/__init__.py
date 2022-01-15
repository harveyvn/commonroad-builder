import unittest

from .test_linear_analyzer import TestLinearAnalyzer


def load_tests(suite, loader):
    suite.addTests(loader.loadTestsFromTestCase(TestLinearAnalyzer))
    return suite