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

        items = [ # (name, version, standard_dirname)
            # Test for a very simple single word name and decimal version number
            ('docutils', '0.5', 'docutils-0.5.dist-info'),
            # Test for another except this time with a '-' in the name, which
            #   needs to be transformed during the name lookup
            ('python-ldap', '2.5', 'python_ldap-2.5.dist-info'),
            # Test for both '-' in the name and a funky version number
            # FIXME The end result, as defined in PEP 376, does not match what
            #   would be acceptable by PEP 386.
            ('python-ldap', '2.5 a---5', 'python_ldap-2.5.a_5.dist-info'),
            ]

        # Import the function in question
        from distutils2._backport.pkgutil import distinfo_dirname

        # Loop through the items to validate the results
        for name, version, standard_dirname in items:
            dirname = distinfo_dirname(name, version)
            self.assertEqual(dirname, standard_dirname)


def test_suite():
    return unittest2.makeSuite(TestPkgUtil)

def test_main():
    run_unittest(test_suite())

if __name__ == "__main__":
    test_main()
