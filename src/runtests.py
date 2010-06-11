"""Tests for distutils2.

The tests for distutils2 are defined in the distutils2.tests package.
"""
import sys

def test_main():
    import distutils2.tests
    from distutils2.tests import run_unittest, reap_children, TestFailed
    from distutils2._backport.tests import test_suite as btest_suite
    # just supporting -q right now
    # to enable detailed/quiet output
    if len(sys.argv) > 1:
        verbose = sys.argv[-1] != '-q'
    else:
        verbose = 1
    try:
        try:
            run_unittest([distutils2.tests.test_suite(), btest_suite()],
                    verbose_=verbose)
            return 0
        except TestFailed:
            return 1
    finally:
        reap_children()

if __name__ == "__main__":
    try:
        from distutils2.tests.support import unittest
    except ImportError:
        print('Error: You have to install unittest2')
        sys.exit(1)

    sys.exit(test_main())

