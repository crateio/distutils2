# -*- encoding: utf-8 -*-
"""Tests for distutils.data."""
import os
import sys
from StringIO import StringIO

from distutils2.tests import unittest, support, run_unittest
from distutils2.datafiles import resources_dests
import re
from os import path as osp




SLASH = re.compile(r'(?<=[^\\])(?:\\{2})*/')

class DataFilesTestCase(support.TempdirManager,
                            support.LoggingCatcher,
                            unittest.TestCase):

    def setUp(self):
        super(DataFilesTestCase, self).setUp()
        self.addCleanup(setattr, sys, 'stdout', sys.stdout)
        self.addCleanup(setattr, sys, 'stderr', sys.stderr)

    def assertFindGlob(self, rules, spec):
        tempdir = self.mkdtemp()
        for filepath in spec:
            filepath = osp.join(tempdir, *SLASH.split(filepath))
            dirname = osp.dirname(filepath)
            if dirname and not osp.exists(dirname):
                os.makedirs(dirname)
            self.write_file(filepath, 'babar')
        for key, value in list(spec.items()):
            if value is None:
                del spec[key]
        result = resources_dests(tempdir, rules)
        self.assertEquals(spec, result)

    def test_simple_glob(self):
        rules = [('', '*.tpl', '{data}')]
        spec  = {'coucou.tpl': '{data}/coucou.tpl',
                 'Donotwant': None}
        self.assertFindGlob(rules, spec)

    def test_multiple_match(self):
        rules = [('scripts', '*.bin', '{appdata}'),
                 ('scripts', '*', '{appscript}')]
        spec  = {'scripts/script.bin': '{appscript}/script.bin',
                 'Babarlikestrawberry': None}
        self.assertFindGlob(rules, spec)

    def test_recursive_glob(self):
        rules = [('', '**/*.bin', '{binary}')]
        spec  = {'binary0.bin': '{binary}/binary0.bin',
                 'scripts/binary1.bin': '{binary}/scripts/binary1.bin',
                 'scripts/bin/binary2.bin': '{binary}/scripts/bin/binary2.bin',
                 'you/kill/pandabear.guy': None}
        self.assertFindGlob(rules, spec)

    def test_final_exemple_glob(self):
        rules = [
            ('mailman/database/schemas/','*', '{appdata}/schemas'),
            ('', '**/*.tpl', '{appdata}/templates'),
            ('', 'developer-docs/**/*.txt', '{doc}'),
            ('', 'README', '{doc}'),
            ('mailman/etc/', '*', '{config}'),
            ('mailman/foo/', '**/bar/*.cfg', '{config}/baz'),
            ('mailman/foo/', '**/*.cfg', '{config}/hmm'),
            ('', 'some-new-semantic.sns', '{funky-crazy-category}')
        ]
        spec = {
            'README': '{doc}/README',
            'some.tpl': '{appdata}/templates/some.tpl',
            'some-new-semantic.sns': '{funky-crazy-category}/some-new-semantic.sns',
            'mailman/database/mailman.db': None,
            'mailman/database/schemas/blah.schema': '{appdata}/schemas/blah.schema',
            'mailman/etc/my.cnf': '{config}/my.cnf',
            'mailman/foo/some/path/bar/my.cfg': '{config}/hmm/some/path/bar/my.cfg',
            'mailman/foo/some/path/other.cfg': '{config}/hmm/some/path/other.cfg',
            'developer-docs/index.txt': '{doc}/developer-docs/index.txt',
            'developer-docs/api/toc.txt': '{doc}/developer-docs/api/toc.txt',
        }
        self.maxDiff = None
        self.assertFindGlob(rules, spec)

def test_suite():
    return unittest.makeSuite(DataFilesTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
