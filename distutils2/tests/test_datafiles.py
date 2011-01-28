# -*- encoding: utf-8 -*-
"""Tests for distutils.data."""
import os
import sys
from StringIO import StringIO

from distutils2.tests import unittest, support, run_unittest
from distutils2.datafiles import resources_dests
import re
from os import path as osp




SLASH = re.compile(r'[^\\](?:\\{2})* ')

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
        result = resources_dests(tempdir, rules)
        self.assertEquals(spec, result)

    def test_simple_glob(self):
        rules = [('*.tpl', '{data}')]
        spec  = {'coucou.tpl': '{data}/coucou.tpl'}
        self.assertFindGlob(rules, spec)

    def test_multiple_match(self):
        rules = [('scripts/*.bin', '{appdata}'),
                 ('scripts/*', '{appscript}')]
        spec  = {'scripts/script.bin': '{appscript}/script.bin'}
        self.assertFindGlob(rules, spec)

    def test_recursive_glob(self):
        rules = [('**/*.bin', '{binary}')]
        spec  = {'binary0.bin': '{binary}/binary0.bin',
                 'scripts/binary1.bin': '{binary}/scripts/binary1.bin',
                 'scripts/bin/binary2.bin': '{binary}/scripts/bin/binary2.bin'}
        self.assertFindGlob(rules, spec)

    def test_final_exemple_glob(self):
        rules = [
            ('mailman/database/schemas/*', '{appdata}/schemas'),
            ('**/*.tpl', '{appdata}/templates'),
            ('developer-docs/**/*.txt', '{doc}'),
            ('README', '{doc}'),
            ('mailman/etc/*', '{config}'),
            ('mailman/foo/**/bar/*.cfg', '{config}/baz'),
            ('mailman/foo/**/*.cfg', '{config}/hmm'),
            ('some-new-semantic.sns', '{funky-crazy-category}')
        ]
        spec = {
            'README': '{doc}/README',
            'some.tpl': '{appdata}/templates/some.tpl',
            'some-new-semantic.sns': '{funky-crazy-category}/some-new-semantic.sns',
            'mailman/database/mailman.db': None,
            'mailman/database/schemas/blah.schema': '{appdata}/schemas/blah.schema',
            'mailman/etc/my.cnf': '{config}/my.cnf',
            'mailman/foo/some/path/bar/my.cfg': '{config}/hmm/some/path/bar/my.cfg',
            'mailman/foo/some/path/other.cfg': '{config}/hmm/some/path/bar/other.cfg',
            'developer-docs/index.txt': '{doc}/index.txt',
            'developer-docs/api/toc.txt': '{doc}/api/toc.txt',
        }
        self.assertFindGlob(rules, spec)
        result = {
            os.path.join('mailman', 'database', 'schemas', 'blah.schema') : set([resources[0][1]]),
            'some.tpl' : set([resources[1][1]]),
            os.path.join('developer-docs', 'index.txt') : set([resources[2][1]]),
            os.path.join('developer-docs', 'api', 'toc.txt') : set([resources[2][1]]),
            'README' : set([resources[3][1]]),
            os.path.join('mailman', 'etc', 'my.cnf') : set([resources[4][1]]),
            os.path.join('mailman', 'foo', 'some', 'path', 'bar', 'my.cfg') : set([resources[5][1], resources[6][1]]),
            os.path.join('mailman', 'foo', 'some', 'path', 'other.cfg') : set([resources[6][1]]),
            'some-new-semantic.sns' : set([resources[7][1]])
        }
        self.assertEquals(find_glob(resources), result)

def test_suite():
    return unittest.makeSuite(DataFilesTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
