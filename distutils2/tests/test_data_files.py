# -*- encoding: utf-8 -*-
"""Tests for distutils.data."""
import os
import sys
from StringIO import StringIO

from distutils2.tests import unittest, support, run_unittest
from distutils2.data.tools import check_glob

class DataFilesTestCase(support.TempdirManager,
                            support.LoggingCatcher,
                            unittest.TestCase):
                            
    def setUp(self):
        super(DataFilesTestCase, self).setUp()
        self.addCleanup(setattr, sys, 'stdout', sys.stdout)
        self.addCleanup(setattr, sys, 'stderr', sys.stderr)
        self.addCleanup(os.chdir, os.getcwd())
    
    def build_example(self):
        os.makedirs(os.path.join('mailman', 'database', 'schemas'))
        os.makedirs(os.path.join('mailman', 'etc'))
        os.makedirs(os.path.join('mailman', 'foo', 'some', 'path', 'bar'))
        os.makedirs(os.path.join('developer-docs', 'api'))
    
        self.write_file('README', '')
        self.write_file('some.tpl', '')
        self.write_file('some-new-semantic.sns', '')
        self.write_file(os.path.join('mailman', 'database', 'mailman.db'), '')
        self.write_file(os.path.join('mailman', 'database', 'schemas', 'blah.schema'), '')
        self.write_file(os.path.join('mailman', 'etc', 'my.cnf'), '')
        self.write_file(os.path.join('mailman', 'foo', 'some', 'path', 'bar', 'my.cfg'), '')
        self.write_file(os.path.join('mailman', 'foo', 'some', 'path', 'other.cfg'), '')
        self.write_file(os.path.join('developer-docs', 'index.txt'), '')
        self.write_file(os.path.join('developer-docs', 'api', 'toc.txt'), '')
               
       
    def test_simple_glob(self):
        tempdir = self.mkdtemp()
        os.chdir(tempdir)
        self.write_file('coucou.tpl', '')
        category = '{data}'
        self.assertEquals(
            check_glob([('*.tpl', category)]),
            {'coucou.tpl' : set([category])})
    
    def test_multiple_glob_same_category(self):
        tempdir = self.mkdtemp()
        os.chdir(tempdir)
        os.mkdir('scripts')
        path = os.path.join('scripts', 'script.bin')
        self.write_file(path, '')
        category = '{appdata}'
        self.assertEquals(
            check_glob(
                [('scripts/*.bin', category), ('scripts/*', category)]),
                {path : set([category])})
    
    def test_multiple_glob_different_category(self):
        tempdir = self.mkdtemp()
        os.chdir(tempdir)
        os.mkdir('scripts')
        path = os.path.join('scripts', 'script.bin')
        self.write_file(path, '')
        category_1 = '{appdata}'
        category_2 = '{appscript}'
        self.assertEquals(
            check_glob(
                [('scripts/*.bin', category_1), ('scripts/*', category_2)]),
                {path : set([category_1, category_2])})
    
    def test_rglob(self):
        tempdir = self.mkdtemp()
        os.chdir(tempdir)
        os.makedirs(os.path.join('scripts', 'bin'))
        path0 = 'binary0.bin'
        path1 = os.path.join('scripts', 'binary1.bin')
        path2 = os.path.join('scripts', 'bin', 'binary2.bin')
        self.write_file(path0, '')
        self.write_file(path1, '')
        self.write_file(path2, '')
        category = '{bin}'
        self.assertEquals(check_glob(
            [('**/*.bin', category)]),
            {path0 : set([category]), path1 : set([category]), path2 : set([category])})
    
    def test_final_exemple_glob(self):
        tempdir = self.mkdtemp()
        os.chdir(tempdir)
        self.build_example()
        resources = [
            ('mailman/database/schemas/*', '{appdata}/schemas'),
            ('**/*.tpl', '{appdata}/templates'),
            ('developer-docs/**/*.txt', '{doc}'),
            ('README', '{doc}'),
            ('mailman/etc/*', '{config}'),
            ('mailman/foo/**/bar/*.cfg', '{config}/baz'),
            ('mailman/foo/**/*.cfg', '{config}/hmm'),
            ('some-new-semantic.sns', '{funky-crazy-category}')
        ]
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
        self.assertEquals(check_glob(resources), result)
            
def test_suite():
    return unittest.makeSuite(DataFilesTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())