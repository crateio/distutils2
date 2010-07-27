import os, sys
from distutils2.core import Command 
import unittest

def get_loader_instance(dotted_path):
    if dotted_path is None:
        return None
    module_name, rest = dotted_path.split('.')[0], dotted_path.split('.')[1:]
    while True:
        try:
            ret = __import__(module_name)
            break
        except ImportError:
            if rest == []:
                return None
            module_name += ('.' + rest[0])
            rest = rest[1:]
    while rest:
        try:
            ret = getattr(ret, rest.pop(0))
        except AttributeError:
            return None
    return ret()

class test(Command):

    description = "" # TODO
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
                    "testLoader": get_loader_instance(self.test_loader)
            }
            if args['testLoader'] is None:
                del args['testLoader']
            unittest.main(**args)
        finally:
            os.chdir(prev_cwd)
