"""Tests for distutils2.run."""

import os
import sys
from StringIO import StringIO

from distutils2 import install
from distutils2.tests import unittest, support
from distutils2.run import main

from distutils2.tests.support import assert_python_ok, assert_python_failure

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


class RunTestCase(support.TempdirManager,
                  support.LoggingCatcher,
                  unittest.TestCase):

    def setUp(self):
        super(RunTestCase, self).setUp()
        self.old_argv = sys.argv, sys.argv[:]

    def tearDown(self):
        sys.argv = self.old_argv[0]
        sys.argv[:] = self.old_argv[1]
        super(RunTestCase, self).tearDown()

    # TODO restore the tests removed six months ago and port them to pysetup

    def test_install(self):
        # making sure install returns 0 or 1 exit codes
        project = os.path.join(os.path.dirname(__file__), 'package.tgz')
        install_path = self.mkdtemp()
        old_get_path = install.get_path
        install.get_path = lambda path: install_path
        old_mod = os.stat(install_path).st_mode
        os.chmod(install_path, 0)
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            self.assertFalse(install.install(project))
            self.assertEqual(main(['install', 'blabla']), 1)
        finally:
            sys.stderr = old_stderr
            os.chmod(install_path, old_mod)
            install.get_path = old_get_path

    def get_pythonpath(self):
        pythonpath = os.environ.get('PYTHONPATH')
        d2parent = os.path.dirname(os.path.dirname(__file__))
        if pythonpath is not None:
            pythonpath = os.pathsep.join((pythonpath, d2parent))
        else:
            pythonpath = d2parent
        return pythonpath

    def test_show_help(self):
        # smoke test, just makes sure some help is displayed
        status, out, err = assert_python_ok(
            '-c', 'from distutils2.run import main; main()', '--help',
            PYTHONPATH=self.get_pythonpath())
        self.assertEqual(status, 0)
        self.assertGreater(out, '')
        self.assertEqual(err, '')

    def test_list_commands(self):
        status, out, err = assert_python_ok(
            '-c', 'from distutils2.run import main; main()', 'run',
            '--list-commands', PYTHONPATH=self.get_pythonpath())
        # check that something is displayed
        self.assertEqual(status, 0)
        self.assertGreater(out, '')
        self.assertEqual(err, '')

        # make sure the manual grouping of commands is respected
        check_position = out.find('  check: ')
        build_position = out.find('  build: ')
        self.assertTrue(check_position, out)  # "out" printed as debugging aid
        self.assertTrue(build_position, out)
        self.assertLess(check_position, build_position, out)

    # TODO test that custom commands don't break --list-commands

    def test_unknown_command_option(self):
        status, out, err = assert_python_failure(
            '-c', 'from distutils2.run import main; main()', 'run', 'build',
            '--unknown', PYTHONPATH=self.get_pythonpath())
        self.assertEqual(status, 1)
        self.assertGreater(out, '')
        # sadly this message comes straight from the getopt module and can't be
        # modified to use repr instead of str for the unknown option; to be
        # changed when the command line parsers are replaced by something clean
        self.assertEqual(err.splitlines()[-1],
                         'error: option --unknown not recognized')

    def test_invalid_command(self):
        status, out, err = assert_python_failure(
            '-c', 'from distutils2.run import main; main()', 'run',
            'com#mand', PYTHONPATH=self.get_pythonpath())
        self.assertEqual(status, 1)
        self.assertGreater(out, 1)
        self.assertEqual(err.splitlines()[-1],
                         "error: invalid command name 'com#mand'")

    def test_unknown_command(self):
        status, out, err = assert_python_failure(
            '-c', 'from distutils2.run import main; main()', 'run',
            'invalid_command', PYTHONPATH=self.get_pythonpath())
        self.assertEqual(status, 1)
        self.assertGreater(out, 1)
        self.assertEqual(err.splitlines()[-1],
                         "error: command 'invalid_command' not recognized")

    def test_unknown_action(self):
        status, out, err = assert_python_failure(
            '-c', 'from distutils2.run import main; main()', 'invalid_action',
            PYTHONPATH=self.get_pythonpath())
        self.assertEqual(status, 1)
        self.assertGreater(out, 1)
        self.assertEqual(err.splitlines()[-1],
                         "error: action 'invalid_action' not recognized")


def test_suite():
    return unittest.makeSuite(RunTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
