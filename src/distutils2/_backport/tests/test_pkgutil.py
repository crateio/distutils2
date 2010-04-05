# -*- coding: utf-8 -*-
"""Tests for PEP 376 pkgutil functionality"""
import unittest2
import sys
import os
import csv
import hashlib

from test.test_support import run_unittest, TESTFN

import distutils2._backport.pkgutil

# TODO Add a test for getting a distribution that is provided by another
#   distribution.

# TODO Add a test for absolute pathed RECORD items (e.g. /etc/myapp/config.ini)

class TestPkgUtilDistribution(unittest2.TestCase):
    """Tests the pkgutil.Distribution class"""

    def setUp(self):
        super(TestPkgUtilDistribution, self).setUp()

        self.fake_dists_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'fake_dists'))
        self.distinfo_dirs = [ os.path.join(self.fake_dists_path, dir)
            for dir in os.listdir(self.fake_dists_path)
            if dir.endswith('.dist-info')
            ]

        def get_hexdigest(file):
            md5_hash = hashlib.md5()
            md5_hash.update(open(file).read())
            return md5_hash.hexdigest()
        def record_pieces(file):
            path = os.path.relpath(file, sys.prefix)
            digest = get_hexdigest(file)
            size = os.path.getsize(file)
            return [path, digest, size]

        self.records = {}
        for distinfo_dir in self.distinfo_dirs:
            # Setup the RECORD file for this dist
            record_file = os.path.join(distinfo_dir, 'RECORD')
            record_writer = csv.writer(open(record_file, 'w'), delimiter=',',
                quoting=csv.QUOTE_NONE)
            dist_location = distinfo_dir.replace('.dist-info', '')

            for path, dirs, files in os.walk(dist_location):
                for f in files:
                    record_writer.writerow(record_pieces(os.path.join(path, f)))
            for file in ['INSTALLER', 'METADATA', 'REQUESTED']:
                record_writer.writerow(record_pieces(
                    os.path.join(distinfo_dir, file)))
            record_writer.writerow([os.path.relpath(record_file, sys.prefix)])
            del record_writer # causes the RECORD file to close
            record_reader = csv.reader(open(record_file, 'rb'))
            record_data = []
            for row in record_reader:
                path, md5, size = row[:] + [ None for i in xrange(len(row), 3) ]
                record_data.append([path, (md5, size,)])
            self.records[distinfo_dir] = dict(record_data)

    def tearDown(self):
        self.records = None
        for distinfo_dir in self.distinfo_dirs:
            record_file = os.path.join(distinfo_dir, 'RECORD')
            open(record_file, 'w').close()
        super(TestPkgUtilDistribution, self).tearDown()

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

    def test_installed_files(self):
        """Test the iteration of installed files."""
        # Test the distribution's installed files
        from distutils2._backport.pkgutil import Distribution
        for distinfo_dir in self.distinfo_dirs:
            dist = Distribution(distinfo_dir)
            for path, md5, size in dist.get_installed_files():
                record_data = self.records[dist.path]
                self.assertTrue(path in record_data.keys())
                self.assertEqual(md5, record_data[path][0])
                self.assertEqual(size, record_data[path][1])

    def test_uses(self):
        """Test to determine if a distribution uses a specified file."""
        # Criteria to test against
        distinfo_name = 'grammar-1.0a4'
        distinfo_dir = os.path.join(self.fake_dists_path,
            distinfo_name + '.dist-info')
        true_path = [self.fake_dists_path, distinfo_name, 'grammar', 'utils.py']
        true_path = os.path.relpath(os.path.join(*true_path), sys.prefix)
        false_path = [self.fake_dists_path, 'towel_stuff-0.1', 'towel_stuff',
            '__init__.py']
        false_path = os.path.relpath(os.path.join(*false_path), sys.prefix)

        # Test if the distribution uses the file in question
        from distutils2._backport.pkgutil import Distribution
        dist = Distribution(distinfo_dir)
        self.assertTrue(dist.uses(true_path))
        self.assertFalse(dist.uses(false_path))

    def test_get_distinfo_file(self):
        """Test the retrieval of dist-info file objects."""
        from distutils2._backport.pkgutil import Distribution
        distinfo_name = 'choxie-2.0.0.9'
        other_distinfo_name = 'grammar-1.0a4'
        distinfo_dir = os.path.join(self.fake_dists_path,
            distinfo_name + '.dist-info')
        dist = Distribution(distinfo_dir)
        # Test for known good file matches
        distinfo_files = [
            # Relative paths
            'INSTALLER', 'METADATA',
            # Absolute paths
            os.path.join(distinfo_dir, 'RECORD'),
            os.path.join(distinfo_dir, 'REQUESTED'),
            ]

        for distfile in distinfo_files:
            value = dist.get_distinfo_file(distfile)
            self.assertTrue(isinstance(value, file))
            # Is it the correct file?
            self.assertEqual(value.name, os.path.join(distinfo_dir, distfile))

        from distutils2.errors import DistutilsError
        # Test an absolute path that is part of another distributions dist-info
        other_distinfo_file = os.path.join(self.fake_dists_path,
            other_distinfo_name + '.dist-info', 'REQUESTED')
        self.assertRaises(DistutilsError, dist.get_distinfo_file,
            other_distinfo_file)
        # Test for a file that does not exist and should not exist
        self.assertRaises(DistutilsError, dist.get_distinfo_file, 'ENTRYPOINTS')

    def test_get_distinfo_files(self):
        """Test for the iteration of RECORD path entries."""
        from distutils2._backport.pkgutil import Distribution
        distinfo_name = 'towel_stuff-0.1'
        distinfo_dir = os.path.join(self.fake_dists_path,
            distinfo_name + '.dist-info')
        dist = Distribution(distinfo_dir)
        # Test for the iteration of the raw path
        distinfo_record_paths = self.records[distinfo_dir].keys()
        found = [ path for path in dist.get_distinfo_files() ]
        self.assertEqual(sorted(found), sorted(distinfo_record_paths))
        # Test for the iteration of local absolute paths
        distinfo_record_paths = [ os.path.join(sys.prefix, path)
            for path in self.records[distinfo_dir].keys()
            ]
        found = [ path for path in dist.get_distinfo_files(local=True) ]
        self.assertEqual(sorted(found), sorted(distinfo_record_paths))


class TestPkgUtilFunctions(unittest2.TestCase):
    """Tests for the new functionality added in PEP 376."""

    def setUp(self):
        super(TestPkgUtilFunctions, self).setUp()
        # Setup the path environment with our fake distributions
        current_path = os.path.abspath(os.path.dirname(__file__))
        self.sys_path = sys.path[:]
        self.fake_dists_path = os.path.join(current_path, 'fake_dists')
        sys.path[0:0] = [self.fake_dists_path]

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
            ('python-ldap', '2.5 a---5', 'python_ldap-2.5 a---5.dist-info'),
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
        """Test for looking up a distribution by name."""
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

        # Verify partial name matching doesn't work
        self.assertEqual(None, get_distribution('towel'))

    def test_get_file_users(self):
        """Test the iteration of distributions that use a file."""
        from distutils2._backport.pkgutil import get_file_users, Distribution
        name = 'towel_stuff-0.1'
        path = os.path.join(self.fake_dists_path, name,
            'towel_stuff', '__init__.py')
        for dist in get_file_users(path):
            self.assertTrue(isinstance(dist, Distribution))
            self.assertEqual(dist.name, name)


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
