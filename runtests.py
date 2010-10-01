#!/usr/bin/env python
"""Tests for distutils2.

The tests for distutils2 are defined in the distutils2.tests package.
"""

import sys


def test_main():
    from distutils2.tests import (run_unittest, reap_children,
                                  test_suite, TestFailed)
    from distutils2._backport.tests import test_suite as btest_suite
    # XXX just supporting -q right now to enable detailed/quiet output
    if len(sys.argv) > 1:
        verbose = sys.argv[-1] != '-q'
    else:
        verbose = 1
    try:
        try:
            run_unittest([test_suite(), btest_suite()], verbose_=verbose)
            return 0
        except TestFailed:
            return 1
    finally:
        reap_children()


if __name__ == "__main__":
    if sys.version < '2.5':
        try:
            from distutils2._backport import hashlib
        except ImportError:
            import subprocess
            subprocess.call([sys.executable, 'setup.py', 'build_ext'])
    sys.exit(test_main())
