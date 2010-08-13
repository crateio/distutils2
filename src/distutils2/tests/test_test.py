import os
import re
import sys
import shutil
import subprocess

from copy import copy
from os.path import join
from StringIO import StringIO
from distutils2.tests.support import unittest, LoggingSilencer, TempdirManager
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


class TestTest(TempdirManager,
               #LoggingSilencer,
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

    @unittest.skipUnless(sys.version > '2.6', 'Need >= 2.6')
    def test_checks_requires(self):
        from distutils2.tests.with_support import examine_warnings
        dist = Distribution()
        dist.tests_require = ['ohno_ohno-impossible_1234-name_stop-that!']
        cmd = test(dist)
        def examinator(ws):
            cmd.ensure_finalized()
            self.assertEqual(1, len(ws))
            warning = ws[0]
            self.assertIs(warning.category, RuntimeWarning)

        examine_warnings(examinator)

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
        

def test_suite():
    return unittest.makeSuite(TestTest)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
