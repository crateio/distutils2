import os, sys
from copy import copy
from os.path import join
from StringIO import StringIO
from distutils2.tests.support import unittest, TempdirManager
from distutils2.command.test import test
import subprocess

TEST_BODY = '''\
import unittest
class SomeTest(unittest.TestCase):
    def test_blah(self):
        self.fail("horribly")
testSuite = unittest.makeSuite(SomeTest)
'''

SETUP_PY = '''\
from distutils2.core import setup
setup(name='somedist',
      version='0.1',
      py_modules=['myowntestmodule', 'somemod'],
)
'''

EXPECTED_OUTPUT = '''\
FAIL: test_blah (myowntestmodule.SomeTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "build/lib/myowntestmodule.py", line 4, in test_blah
    self.fail("horribly")
AssertionError: horribly
'''

class TestTest(TempdirManager, unittest.TestCase):

    def setUp(self):
        super(TestTest, self).setUp()
        self.pkg_dir = self.prepare_dist()
        self.cwd = os.getcwd()
        os.chdir(self.pkg_dir)
        self.orig_environ = copy(os.environ)
        distutils2path = join(__file__, '..', '..', '..')
        distutils2path = os.path.abspath(distutils2path)
        self.old_pythonpath = os.environ.get('PYTHONPATH', '')
        os.environ['PYTHONPATH'] = distutils2path + ":" + self.old_pythonpath

    def tearDown(self):
        super(TestTest, self).tearDown()
        os.chdir(self.cwd)
        os.environ['PYTHONPATH'] = self.old_pythonpath

    def prepare_dist(self):
        # prepare distribution
        pkg_dir = self.mkdtemp()
        self.write_file(join(pkg_dir, "setup.py"), SETUP_PY)
        self.write_file(join(pkg_dir, "somemod.py"), "")
        self.write_file(join(pkg_dir, "myowntestmodule.py"), TEST_BODY)
        return pkg_dir

    def test_runs_simple_tests(self):
        command = [sys.executable, "setup.py", "test"]
        command += ['--test-suite', 'myowntestmodule']
        test_proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        _, errors = test_proc.communicate()

        # ensure right output
        self.assertIn(EXPECTED_OUTPUT, errors)

    def _test_setup_py_accepts_options(self):
        pass

    def _test_options_preparation(self):
        pass
