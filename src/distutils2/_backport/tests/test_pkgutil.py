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

    def test_distinfo_dirname(self):
        """Given a name and a version, we expect the distinfo_dirname function
        to return a standard distribution information directory name."""
        # Test for a very simple single word name and decimal version number
        name = 'docutils'
        version = '0.5'
        standard_dirname = 'docutils-0.5.dist-info'

        from distutils2._backport.pkgutil import distinfo_dirname
        dirname = distinfo_dirname(name, version)
        self.assertEqual(dirname, standard_dirname)

        # Test for another except this time with a '-' in the name, which
        #   needs to be transformed during the name lookup
        name = 'python-ldap'
        version = '2.5'
        standard_dirname = 'python_ldap-2.5.dist-info'

        from distutils2._backport.pkgutil import distinfo_dirname
        dirname = distinfo_dirname(name, version)
        self.assertEqual(dirname, standard_dirname)


def test_suite():
    return unittest2.makeSuite(TestPkgUtil)

def test_main():
    run_unittest(test_suite())

if __name__ == "__main__":
    test_main()
