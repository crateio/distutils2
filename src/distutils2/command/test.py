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
        self.test_suite = self.distribution.test_suite

    def distpath(self):
        self.run_command('build')
        build_cmd = self.get_finalized_command("build")
        return os.path.join(build_cmd.build_base, "lib")

    def run(self):
        orig_path = sys.path[:]
        try:
            sys.path.insert(0, self.distpath())
            unittest.main(module=self.test_suite, argv=sys.argv[:1])
        finally:
            sys.path[:] = orig_path
