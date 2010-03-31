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

    def test_get_distributions(self):
        """Lookup all distributions found in the ``sys.path``."""
        # This test could potentially pick up other installed distributions
        fake_dists = [('grammar', '1.0a4'), ('choxie', '2009'),
            ('towel-stuff', '0.1')]
        found_dists = []

        # Setup the path environment with our fake distributions
        current_path = os.path.abspath(os.path.dirname(__file__))
        sys.path[0:0] = [os.path.join(current_path, 'fake_dists')]

        # Import the function in question
        from distutils2._backport.pkgutil import get_distributions, Distribution

        # Verify the fake dists have been found.
        dists = [ dist for dist in get_distributions() ]
        for dist in dists:
            if not isinstance(dist, Distribution):
                self.fail("item received was not a Distribution instance: "
                    "%s" % type(dist))
            if dist.name in dict(fake_dists).keys():
                found_dists.append((dist.name, dist.metadata.version,))
            # otherwise we don't care what other distributions are found

        # Finally, test that we found all that we were looking for
        self.assertListEqual(found_dists, dict(fake_dists).keys())



def test_suite():
    return unittest2.makeSuite(TestPkgUtil)

def test_main():
    run_unittest(test_suite())

if __name__ == "__main__":
    test_main()
