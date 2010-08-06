#!/usr/bin/env python
"""Tests for distutils2.

The tests for distutils2 are defined in the distutils2.tests package.
"""

import sys
from os.path import dirname, islink, realpath, join, abspath
from optparse import OptionParser

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
    # A function like that is needed because some GNU/Linux
    # distributions, such a Ubuntu, really like to build link farm in
    # /usr/lib in order to save a few bytes on the disk.
    dirnames = [dirname(module.__file__)]

    pymod = module.__file__.rstrip("c")
    if islink(pymod):
        dirnames.append(dirname(realpath(pymod)))
    return dirnames


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


def coverage_report(opts):
    from distutils2.tests.support import unittest
    cov = get_coverage()
    if hasattr(cov, "load"):
        # running coverage 3.x
        cov.load()
        morfs = None
    else:
        morfs = "distutils2/*"
        # running coverage 2.x
        cov.cache = COVERAGE_FILE
        cov.restore()

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

    cov.report(morfs, omit_prefixes=prefixes, show_missing=opts.show_missing)


def test_main():
    opts, args = parse_opts()
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


def run_tests(verbose):
    import distutils2.tests
    from distutils2.tests import run_unittest, reap_children, TestFailed
    from distutils2._backport.tests import test_suite as btest_suite
    # XXX just supporting -q right now to enable detailed/quiet output
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
        sys.stderr.write('Error: You have to install unittest2')
        sys.exit(1)
    sys.exit(test_main())
