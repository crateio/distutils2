"""Tests for distutils.extension."""
import os
import warnings

from distutils2.extension import Extension
from distutils2.tests.support import unittest

class ExtensionTestCase(unittest.TestCase):

    pass

def test_suite():
    return unittest.makeSuite(ExtensionTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
