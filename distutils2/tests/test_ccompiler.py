"""Tests for distutils.ccompiler."""
from distutils2.tests import unittest, support


class CCompilerTestCase(support.EnvironGuard, unittest.TestCase):

    pass  # XXX need some tests on CCompiler


def test_suite():
    return unittest.makeSuite(CCompilerTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
