"""Tests for distutils2.run."""

import StringIO
import os
import shutil
import sys

import distutils2
from distutils2.tests import captured_stdout
from distutils2.tests import unittest, support

# setup script that uses __file__
setup_using___file__ = """\

__file__

from distutils2.run import setup
setup()
"""

setup_prints_cwd = """\

import os
print os.getcwd()

from distutils2.run import setup
setup()
"""


class CoreTestCase(support.EnvironGuard, unittest.TestCase):

    def setUp(self):
        super(CoreTestCase, self).setUp()
        self.old_stdout = sys.stdout
        self.cleanup_testfn()
        self.old_argv = sys.argv, sys.argv[:]

    def tearDown(self):
        sys.stdout = self.old_stdout
        self.cleanup_testfn()
        sys.argv = self.old_argv[0]
        sys.argv[:] = self.old_argv[1]
        super(CoreTestCase, self).tearDown()

    def cleanup_testfn(self):
        path = distutils2.tests.TESTFN
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)

    def write_setup(self, text, path=distutils2.tests.TESTFN):
        open(path, "w").write(text)
        return path

def test_suite():
    return unittest.makeSuite(CoreTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
