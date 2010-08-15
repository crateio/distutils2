import os
import re
import sys
import shutil
import subprocess

from copy import copy
from os.path import join
from StringIO import StringIO
from distutils2.tests.support import unittest, WarningsCatcher, TempdirManager
from distutils2.command.test import test
from distutils2.dist import Distribution

try:
    any
except NameError:
    from distutils2._backport import any

EXPECTED_OUTPUT_RE = r'''FAIL: test_blah \(myowntestmodule.SomeTest\)
----------------------------------------------------------------------
Traceback \(most recent call last\):
  File ".+/myowntestmodule.py", line \d+, in test_blah
    self.fail\("horribly"\)
AssertionError: horribly
'''

here = os.path.dirname(os.path.abspath(__file__))

def with_mock_ut2_module(func):
    def wrapper(*args):
        class MockUTModule(object): pass
        class MockUTClass(object):
            def __init__(*_, **__): pass
            def discover(self): pass
            def run(self, _): pass
        ut2 = MockUTModule()
        ut2.TestLoader = MockUTClass
        ut2.TextTestRunner = MockUTClass
        orig_ut2 = sys.modules.get('unittest2', None)
        try:
            sys.modules['unittest2'] = ut2
            args += (ut2,)
            func(*args)
        finally:
            if orig_ut2 is not None:
                sys.modules['unittest2'] = orig_ut2
            else:
                del sys.modules['unittest2']
    return wrapper

def with_ut_isolated(func):
    def wrapper(*args):
        import unittest as ut1

        orig_discover = getattr(ut1.TestLoader, 'discover', None)
        try:
            args += (ut1,)
            return func(*args)
        finally:
            if orig_discover is not None:
                ut1.TestLoader.discover = orig_discover
    return wrapper

class TestTest(TempdirManager,
               WarningsCatcher,
               unittest.TestCase):

    def setUp(self):
        super(TestTest, self).setUp()

        distutils2path = os.path.dirname(os.path.dirname(here))
        self.old_pythonpath = os.environ.get('PYTHONPATH', '')
        os.environ['PYTHONPATH'] = distutils2path + os.pathsep + self.old_pythonpath

    def tearDown(self):
        os.environ['PYTHONPATH'] = self.old_pythonpath
        super(TestTest, self).tearDown()

    def assert_re_match(self, pattern, string):
        def quote(s):
            lines = ['## ' + line for line in s.split('\n')]
            sep = ["#" * 60]
            return [''] + sep + lines + sep
        msg = quote(pattern) + ["didn't match"] + quote(string)
        msg = "\n".join(msg)
        if not re.search(pattern, string):
            self.fail(msg)

    def run_with_dist_cwd(self, pkg_dir):
        cwd = os.getcwd()
        command = [sys.executable, "setup.py", "test"]
        try:
            os.chdir(pkg_dir)
            test_proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            _, errors = test_proc.communicate()
            return errors
        finally:
            os.chdir(cwd)

    def prepare_dist(self, dist_name):
        pkg_dir = join(os.path.dirname(__file__), "dists", dist_name)
        temp_pkg_dir = join(self.mkdtemp(), dist_name)
        shutil.copytree(pkg_dir, temp_pkg_dir)
        return temp_pkg_dir

    def test_runs_simple_tests(self):
        self.pkg_dir = self.prepare_dist('simple_test')
        output = self.run_with_dist_cwd(self.pkg_dir)
        self.assert_re_match(EXPECTED_OUTPUT_RE, output)
        self.assertFalse(os.path.exists(join(self.pkg_dir, 'build')))

    def test_builds_extensions(self):
        self.pkg_dir = self.prepare_dist("extensions_test")
        output = self.run_with_dist_cwd(self.pkg_dir)
        self.assert_re_match(EXPECTED_OUTPUT_RE, output)
        self.assertTrue(os.path.exists(join(self.pkg_dir, 'build')))
        self.assertTrue(any(x.startswith('lib') for x in os.listdir(join(self.pkg_dir, 'build'))))

    def _test_works_with_2to3(self):
        pass

    def test_checks_requires(self):
        dist = Distribution()
        cmd = test(dist)
        phony_project = 'ohno_ohno-impossible_1234-name_stop-that!'
        cmd.tests_require = [phony_project]
        record = []
        cmd.announce = lambda *args: record.append(args)
        cmd.ensure_finalized()
        self.assertEqual(1, len(record))
        self.assertIn(phony_project, record[0][0])

    def test_custom_runner(self):
        dist = Distribution()
        cmd = test(dist)

        tmp_dir = self.mkdtemp()
        try:
            sys.path.append(tmp_dir)
            self.write_file(os.path.join(tmp_dir, 'distutils2_tests_a.py'), '')
            import distutils2_tests_a as a_module
            a_module.recorder = lambda: record.append("runner called")
            record = []
            cmd.runner = "distutils2_tests_a.recorder"
            cmd.ensure_finalized()
            cmd.run()
            self.assertEqual(["runner called"], record)
        finally:
            sys.path.remove(tmp_dir)

    @with_ut_isolated
    @with_mock_ut2_module
    def test_gets_unittest_discovery(self, ut1, mock_ut2):
        dist = Distribution()
        cmd = test(dist)
        ut1.TestLoader.discover = lambda: None
        self.assertEqual(cmd.get_ut_with_discovery(), ut1)

        del ut1.TestLoader.discover
        self.assertEqual(cmd.get_ut_with_discovery(), mock_ut2)

    @with_ut_isolated
    @with_mock_ut2_module
    def test_calls_discover(self, ut1, mock_ut2):
        if hasattr(ut1.TestLoader, "discover"):
            del ut1.TestLoader.discover
        record = []
        mock_ut2.TestLoader.discover = lambda self, path: record.append(path)
        dist = Distribution()
        cmd = test(dist)
        cmd.run()
        self.assertEqual(record, [os.curdir])

def test_suite():
    return unittest.makeSuite(TestTest)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
