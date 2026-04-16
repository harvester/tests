"""
Pre-run modifier that removes all teardowns before execution.

Usage:
    robot --prerunmodifier skip_teardown.SkipSuiteTeardown ...
"""
from robot.api import SuiteVisitor


class SkipSuiteTeardown(SuiteVisitor):
    """Removes suite and test level teardowns so resources are preserved."""

    def start_suite(self, suite):
        suite.teardown = None

    def start_test(self, test):
        test.teardown = None
