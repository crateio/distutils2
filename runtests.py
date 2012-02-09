#!/usr/bin/env python
"""Test runner for distutils2.

The tests for distutils2 are defined in the distutils2.tests package.
They can also be executed with the unittest2 runner or nose.
"""

import os
import sys
from os.path import dirname, islink, realpath, join, abspath
from optparse import OptionParser
from distutils2.tests import unittest


# unittest machinery copied from stdlib's test.regrtest and test.support

class TestFailed(Exception):
    """Test failed."""


class BasicTestRunner(object):
    def run(self, test):
        result = unittest.TestResult()
        test(result)
        return result


def reap_children():
    """Use this function at the end of test_main() whenever sub-processes
    are started.  This will help ensure that no extra children (zombies)
    stick around to hog resources and create problems when looking
    for refleaks.
    """

    # Reap all our dead child processes so we don't leave zombies around.
    # These hog resources and might be causing some of the buildbots to die.
    if hasattr(os, 'waitpid'):
        any_process = -1
        while True:
            try:
                # This will raise an exception on Windows.  That's ok.
                pid, status = os.waitpid(any_process, os.WNOHANG)
                if pid == 0:
                    break
            except:
                break


def _run_suite(suite, verbose=True):
    """Run tests from a unittest.TestSuite-derived class."""
    if verbose:
        runner = unittest.TextTestRunner(sys.stdout, verbosity=2)
    else:
        runner = BasicTestRunner()

    result = runner.run(suite)
    if not result.wasSuccessful():
        if len(result.errors) == 1 and not result.failures:
            err = result.errors[0][1]
        elif len(result.failures) == 1 and not result.errors:
            err = result.failures[0][1]
        else:
            err = "errors occurred; run in verbose mode for details"
        raise TestFailed(err)


def run_unittest(classes, verbose=True):
    """Run tests from unittest.TestCase-derived classes.

    Originally extracted from stdlib test.test_support and modified to
    support unittest2.
    """
    valid_types = (unittest.TestSuite, unittest.TestCase)
    suite = unittest.TestSuite()
    for cls in classes:
        if isinstance(cls, basestring):
            if cls in sys.modules:
                suite.addTest(unittest.findTestCases(sys.modules[cls]))
            else:
                raise ValueError("str arguments must be keys in sys.modules")
        elif isinstance(cls, valid_types):
            suite.addTest(cls)
        else:
            suite.addTest(unittest.makeSuite(cls))
    _run_suite(suite, verbose)


def run_tests(verbose):
    # do NOT import those at the top level, coverage will be inaccurate if
    # distutils2 modules are imported before coverage magic is started
    from distutils2.tests import test_suite
    from distutils2._backport.tests import test_suite as btest_suite
    try:
        try:
            run_unittest([test_suite(), btest_suite()], verbose=verbose)
            return 0
        except TestFailed:
            return 1
    finally:
        reap_children()


# coverage-related code

COVERAGE_FILE = join(dirname(abspath(__file__)), '.coverage')


def get_coverage():
    """ Return a usable coverage object. """
    # deferred import because coverage is optional
    import coverage
    cov = getattr(coverage, "the_coverage", None)
    if not cov:
        cov = coverage.coverage(COVERAGE_FILE)
    return cov


def ignore_prefixes(module):
    """ Return a list of prefixes to ignore in the coverage report if
    we want to completely skip `module`.
    """
    # A function like that is needed because some operating systems like Debian
    # and derivatives use symlinks directory in order to save disk space
    dirnames = [dirname(module.__file__)]

    pymod = module.__file__.rstrip('co')
    if islink(pymod):
        dirnames.append(dirname(realpath(pymod)))
    return dirnames


def coverage_report(opts):
    from distutils2.tests.support import unittest
    cov = get_coverage()
    if hasattr(cov, "load"):
        # running coverage 3.x
        cov.load()
        # morfs means modules or files
        morfs = None
    else:
        # running coverage 2.x
        cov.cache = COVERAGE_FILE
        cov.restore()
        morfs = [m for m in cov.cexecuted if "distutils2" in m]

    prefixes = ["runtests", "distutils2/tests", "distutils2/_backport"]
    prefixes += ignore_prefixes(unittest)

    try:
        import docutils
        prefixes += ignore_prefixes(docutils)
    except ImportError:
        # that module is completely optional
        pass

    try:
        import roman
        prefixes += ignore_prefixes(roman)
    except ImportError:
        # that module is also completely optional
        pass

    try:
        cov.report(morfs,
                   omit_prefixes=prefixes,
                   show_missing=opts.show_missing)
    except TypeError:
        # Coverage 3.4 turned `omit_prefixes` into a list of globbing patterns
        cov.report(morfs,
                   omit=[p + "*" for p in prefixes],
                   show_missing=opts.show_missing)


# command-line parsing

def parse_opts():
    parser = OptionParser(usage="%prog [OPTIONS]",
                          description="run the distutils2 unittests")

    parser.add_option("-q", "--quiet", help="do not print verbose messages",
                      action="store_true", default=False)
    parser.add_option("-c", "--coverage", action="store_true", default=False,
                      help="produce a coverage report at the end of the run")
    parser.add_option("-r", "--report", action="store_true", default=False,
                      help="produce a coverage report from the last test run")
    parser.add_option("-m", "--show-missing", action="store_true",
                      default=False,
                      help=("Show line numbers of statements in each module "
                            "that weren't executed."))

    opts, args = parser.parse_args()
    return opts, args


def test_main():
    opts, args = parse_opts()
    # FIXME when we run with --quiet, we still want to see errors and failures
    verbose = not opts.quiet
    ret = 0

    if opts.coverage:
        cov = get_coverage()
        cov.erase()
        cov.start()
    if not opts.report:
        ret = run_tests(verbose)
    if opts.coverage:
        cov.stop()
        cov.save()

    if opts.report or opts.coverage:
        coverage_report(opts)

    return ret


if __name__ == "__main__":
    if sys.version_info[:2] < (2, 5):
        try:
            from distutils2._backport import hashlib
        except ImportError:
            import subprocess
            subprocess.call([sys.executable, 'setup.py', 'build_ext'])
    sys.exit(test_main())
