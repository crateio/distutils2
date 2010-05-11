"""Tests for distutils.converter."""
import unittest2
from distutils2.converter import DistutilsRefactoringTool

_ORIGINAL = """\
from distutils.core import setup

setup(name='Foo')
"""

_WANTED = """\
from distutils2.core import setup

setup(name='Foo')
"""
class ConverterTestCase(unittest2.TestCase):

    def test_import(self):
        # simplest case: renaming distutils import in setup.py
        ref = DistutilsRefactoringTool()
        res = ref.refactor_string(_ORIGINAL, 'setup.py')
        self.assertEquals(str(res), _WANTED)

def test_suite():
    return unittest2.makeSuite(ConverterTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
