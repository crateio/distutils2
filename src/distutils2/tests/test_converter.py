"""Tests for distutils.converter."""
import os
import sys
import unittest2
from distutils2.converter import DistutilsRefactoringTool

_CURDIR = os.path.dirname(__file__)

def _read_file(path):
    # yes, distutils2 is 2.4 compatible, so, no with...
    f = open(path)
    try:
        return f.read()
    finally:
        f.close()


class ConverterTestCase(unittest2.TestCase):

    @unittest2.skipUnless(not sys.version < '2.6', 'Needs Python >=2.6')
    def test_conversions(self):
        # for all XX_before in the conversions/ dir
        # we run the refactoring tool
        ref = DistutilsRefactoringTool()
        convdir = os.path.join(_CURDIR, 'conversions')
        for file_ in os.listdir(convdir):
            if 'after' in file_ or not file_.endswith('py'):
                continue
            original = _read_file(os.path.join(convdir, file_))
            wanted = file_.replace('before', 'after')
            wanted = _read_file(os.path.join(convdir, wanted))
            res = ref.refactor_string(original, 'setup.py')
            self.assertEquals(str(res), wanted)

def test_suite():
    return unittest2.makeSuite(ConverterTestCase)

if __name__ == '__main__':
    unittest2.main(defaultTest="test_suite")
