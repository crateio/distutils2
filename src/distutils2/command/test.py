import os
import sys
from distutils2 import log
from distutils2.core import Command
from distutils2._backport.pkgutil import get_distribution
from distutils2.util import resolve_name
import unittest
import warnings

class test(Command):

    description = "run the distribution's test suite"

    user_options = [
        ('suite=', 's',
            "Test suite to run (e.g. 'some_module.test_suite')"),
        ('runner=', None,
            "Test runner to be called."),
        ('tests-require=', None,
            "List of packages required to run the test suite."),
    ]

    def initialize_options(self):
        self.suite = None
        self.runner = None
        self.tests_require = []

    def finalize_options(self):
        self.build_lib = self.get_finalized_command("build").build_lib
        for requirement in self.tests_require:
            if get_distribution(requirement) is None:
                warnings.warn("The test dependency %s is not installed which may couse the tests to fail." % requirement,
                              RuntimeWarning)
        if not self.suite and not self.runner and self.get_ut_with_discovery() is None:
            self.announce("No test discovery available. Please specify the 'suite' or 'runner' option or install unittest2.", log.ERROR)
    
    def get_ut_with_discovery(self):
        if hasattr(unittest.TestLoader, "discover"):
            return unittest
        else:
            try:
                import unittest2
                return unittest2
            except ImportError:
                return None

    def run(self):
        prev_cwd = os.getcwd()
        try:
            # build distribution if needed
            if self.distribution.has_ext_modules():
                build = self.get_reinitialized_command('build')
                build.inplace = 1
                self.run_command('build')
                os.chdir(self.build_lib)

            # run the tests
            if self.runner:
                resolve_name(self.runner)()
            elif self.suite:
                unittest.TextTestRunner(verbosity=self.verbose + 1).run(resolve_name(self.suite)())
            elif self.get_ut_with_discovery():
                discovery_ut = self.get_ut_with_discovery()
                test_suite = discovery_ut.TestLoader().discover(os.curdir)
                discovery_ut.TextTestRunner(verbosity=self.verbose + 1).run(test_suite)
        finally:
            os.chdir(prev_cwd)
