"""Tests for distutils.config."""
import sys
import os
import copy

from distutils2.tests import support, run_unittest
from distutils2.tests.support import unittest


SETUP_CFG = """
[metadata]
version = 1.0
author = tarek
author_email = tarek@ziade.org
"""

class ConfigTestCase(support.TempdirManager,
                     unittest.TestCase):

    def test_config(self):
        tempdir = self.mkdtemp()
        setup_cfg = os.path.join(tempdir, 'setup.cfg')
        f = open(setup_cfg, 'w')
        try:
            f.write(SETUP_CFG)
        finally:
            f.close()

        # trying to load the metadata now
        old_args = copy.copy(sys.argv)
        sys.argv[:] = ['setup.py', '--version']
        old_wd = os.getcwd()
        os.chdir(tempdir)
        try:
            from distutils2.core import setup
            dist = setup()
        finally:
            os.chdir(old_wd)
            sys.argv[:] = old_args

        # check what was done
        self.assertEqual(dist.metadata['Author'], 'tarek')
        self.assertEqual(dist.metadata['Author-Email'], 'tarek@ziade.org')
        self.assertEqual(dist.metadata['Version'], '1.0')


def test_suite():
    return unittest.makeSuite(ConfigTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
