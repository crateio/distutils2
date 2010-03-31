# -*- coding: utf-8 -*-
"""Tests for PEP 376 pkgutil functionality"""
import unittest2
import sys
import os

from test.test_support import run_unittest, TESTFN

import distutils2._backport.pkgutil


class TestPkgUtilDistribution(unittest2.TestCase):
    """Tests the pkgutil.Distribution class"""

    def test_instantiation(self):
        """Test the Distribution class's instantiation provides us with usable
        attributes."""
        # Import the Distribution class
        from distutils2._backport.pkgutil import distinfo_dirname, Distribution

        here = os.path.abspath(os.path.dirname(__file__))
        name = 'choxie'
        version = '2.0.0.9'
        dist_path = os.path.join(here, 'fake_dists',
            distinfo_dirname(name, version))
        dist = Distribution(dist_path)

        self.assertEqual(dist.name, name)
        from distutils2.metadata import DistributionMetadata
        self.assertTrue(isinstance(dist.metadata, DistributionMetadata))
        self.assertEqual(dist.metadata['version'], version)
        self.assertTrue(isinstance(dist.requested, type(bool())))


class TestPkgUtilFunctions(unittest2.TestCase):
    """Tests for the new functionality added in PEP 376."""

    def setUp(self):
        super(TestPkgUtilFunctions, self).setUp()
        # Setup the path environment with our fake distributions
        current_path = os.path.abspath(os.path.dirname(__file__))
        self.sys_path = sys.path[:]
        sys.path[0:0] = [os.path.join(current_path, 'fake_dists')]

    def tearDown(self):
        super(TestPkgUtilFunctions, self).tearDown()
        sys.path[:] = self.sys_path

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
        fake_dists = [('grammar', '1.0a4'), ('choxie', '2.0.0.9'),
            ('towel-stuff', '0.1')]
        found_dists = []

        # Import the function in question
        from distutils2._backport.pkgutil import get_distributions, Distribution

        # Verify the fake dists have been found.
        dists = [ dist for dist in get_distributions() ]
        for dist in dists:
            if not isinstance(dist, Distribution):
                self.fail("item received was not a Distribution instance: "
                    "%s" % type(dist))
            if dist.name in dict(fake_dists).keys():
                found_dists.append((dist.name, dist.metadata['version'],))
            # otherwise we don't care what other distributions are found

        # Finally, test that we found all that we were looking for
        self.assertListEqual(sorted(found_dists), sorted(fake_dists))

    def test_get_distribution(self):
        """Lookup a distribution by name."""
        # Test the lookup of the towel-stuff distribution
        name = 'towel-stuff' # Note: This is different from the directory name

        # Import the function in question
        from distutils2._backport.pkgutil import get_distribution, Distribution

        # Lookup the distribution
        dist = get_distribution(name)
        self.assertTrue(isinstance(dist, Distribution))
        self.assertEqual(dist.name, name)

        # Verify that an unknown distribution returns None
        self.assertEqual(None, get_distribution('bogus'))


def test_suite():
    suite = unittest2.TestSuite()
    testcase_loader = unittest2.loader.defaultTestLoader.loadTestsFromTestCase
    suite.addTest(testcase_loader(TestPkgUtilFunctions))
    suite.addTest(testcase_loader(TestPkgUtilDistribution))
    return suite

def test_main():
    run_unittest(test_suite())

if __name__ == "__main__":
    test_main()
