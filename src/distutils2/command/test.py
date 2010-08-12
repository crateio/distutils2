import os, sys
from distutils2.core import Command 
from distutils2._backport.pkgutil import get_distribution
from distutils2.util import resolve_dotted_name
import unittest
import warnings

class test(Command):

    description = "run the distribution's test suite"
    user_options = [
        ('test-suite=', 's',
            "Test suite to run (e.g. 'some_module.test_suite')"),
        ('test-loader=', None,
            "Test loader to be used to load the test suite."),
    ]
    
    def initialize_options(self):
        self.test_suite  = None
        self.test_loader = None
    
    def finalize_options(self):
        self.build_lib = self.get_finalized_command("build").build_lib
        if self.distribution.tests_require:
            for requirement in self.distribution.tests_require:
                if get_distribution(requirement) is None:
                    warnings.warn("The test dependency %s is not installed which may couse the tests to fail.",
                                  RuntimeWarning)

    def run(self):
        prev_cwd = os.getcwd()
        try:
            if self.distribution.has_ext_modules():
                build = self.get_reinitialized_command('build')
                build.inplace = 1 # TODO - remove make sure it's needed
                self.run_command('build')
                os.chdir(self.build_lib)
            args = {"module": self.test_suite,
                    "argv": sys.argv[:1],
                    "testLoader": resolve_dotted_name(self.test_loader)
            }
            if args['testLoader'] is None:
                del args['testLoader']
            unittest.main(**args)
        finally:
            os.chdir(prev_cwd)
