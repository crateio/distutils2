import os, sys
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
    ]

    def initialize_options(self):
        self.suite = None
        self.runner = None

    def finalize_options(self):
        self.build_lib = self.get_finalized_command("build").build_lib
        if self.distribution.tests_require:
            for requirement in self.distribution.tests_require:
                if get_distribution(requirement) is None:
                    warnings.warn("The test dependency %s is not installed which may couse the tests to fail." % requirement,
                                  RuntimeWarning)
        if not self.suite and not self.runner:
            self.announce("Either 'suite' or 'runner' option must be specified", log.ERROR)

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
                unittest.main(None, None, [unittest.__file__, '--verbose', self.suite])
        finally:
            os.chdir(prev_cwd)
