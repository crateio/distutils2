#!/usr/bin/env python
"""Tests for distutils2.

The tests for distutils2 are defined in the distutils2.tests package.
"""

# TODO:

# The coverage report is only accurate when ran inside a virtualenv
# created with the --no-site-packages option.  When it's not the case,
# the built-in ignore list is not accurate and third party packages
# show-up in the report, lowering the overall coverage.  

# One particular problem it docutils on Ubuntu which has a __file__
# starting with /usr/lib/python2.6 while the path in the coverage
# report starts with /usr/share/pyshared.

import sys
from os.path import dirname
from optparse import OptionParser

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
    import coverage
    import unittest2
    import docutils
    cov = coverage.coverage()
    cov.load()

    cov.report(omit_prefixes=["distutils2/tests", 
                              "runtests", 
                              "distutils2/_backport", 
                              dirname(unittest2.__file__),
                              dirname(dirname(docutils.__file__))], 
               show_missing=opts.show_missing)


def test_main():
    opts, args = parse_opts()
    verbose = not opts.quiet
    ret = 0
    
    if opts.coverage or opts.report:
        import coverage
        
    if opts.coverage:
        cov = coverage.coverage()
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

