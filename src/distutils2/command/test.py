import os, sys
from distutils2.core import Command 
import unittest

class test(Command):

    description = "" # TODO
    user_options = [
        ('test-suite=','s',
            "Test suite to run (e.g. 'some_module.test_suite')"),
    ]
    
    def initialize_options(self):
        self.test_suite = None
    
    def finalize_options(self):
        self.build_lib = self.get_finalized_command("build").build_lib

    def run(self):
        prev_cwd = os.getcwd()
        try:
            if self.distribution.has_ext_modules():
                build = self.get_reinitialized_command('build')
                build.inplace = 1
                self.run_command('build')
                os.chdir(self.build_lib)
            unittest.main(module=self.test_suite, argv=sys.argv[:1])
        finally:
            os.chdir(prev_cwd)
