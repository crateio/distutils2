# -*- coding: utf-8 -*-
"""Tests for PEP 376 pkgutil functionality"""
import unittest2
import sys
import os

from test.test_support import run_unittest, TESTFN

import distutils2._backport.pkgutil

class TestPkgUtil(unittest2.TestCase):
    """Tests for the new functionality added in PEP 376."""

    # def setUp(self):
    #     super(TestPkgUtil, self).setUp()

    # def tearDown(self):
    #     super(TestPkgUtil, self).tearDown()

    def test_something(self):
        pass


def test_suite():
    return unittest2.makeSuite(TestPkgUtil)

def test_main():
    run_unittest(test_suite())

if __name__ == "__main__":
    test_main()
