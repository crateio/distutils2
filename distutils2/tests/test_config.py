"""Tests for distutils.config."""
import os
import sys
from StringIO import StringIO

from distutils2.core import setup
from distutils2.tests import unittest, support, run_unittest


SETUP_CFG = """
[metadata]
version = 1.0
author = tarek
author_email = tarek@ziade.org
"""

class ConfigTestCase(support.TempdirManager,
                     unittest.TestCase):

    def setUp(self):
        super(ConfigTestCase, self).setUp()
        self.addCleanup(setattr, sys, 'argv', sys.argv[:])
        self.addCleanup(setattr, sys, 'stdout', sys.stdout)
        self.addCleanup(os.chdir, os.getcwd())

    def test_config(self):
        tempdir = self.mkdtemp()
        os.chdir(tempdir)
        self.write_file('setup.cfg', SETUP_CFG)

        # try to load the metadata now
        sys.stdout = StringIO()
        sys.argv[:] = ['setup.py', '--version']
        dist = setup()
        # sanity check
        self.assertEqual(sys.stdout.getvalue(), '1.0' + os.linesep)

        # check what was done
        self.assertEqual(dist.metadata['Author'], 'tarek')
        self.assertEqual(dist.metadata['Author-Email'], 'tarek@ziade.org')
        self.assertEqual(dist.metadata['Version'], '1.0')


def test_suite():
    return unittest.makeSuite(ConfigTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
