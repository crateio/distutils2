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
       
    def test_simple_check_glob(self):
        tempdir = self.mkdtemp()
        os.chdir(tempdir)
        self.write_file('coucou.tpl', '')
        category = '{data}'
        self.assertEquals(
            check_glob([('*.tpl', category)]),
            {'coucou.tpl' : [category]})
    
    def test_multiple_glob_same_category(self):
        tempdir = self.mkdtemp()
        os.chdir(tempdir)
        os.mkdir('scripts')
        path = os.path.join('scripts', 'script.bin')
        self.write_file(path, '')
        category = '{appdata}'
        self.assertEquals(
            check_glob(
                [('**/*.bin', category), ('scripts/*', category)]),
                {path : [category]})
    
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
                [('**/*.bin', category_1), ('scripts/*', category_2)]),
                {path : [category_1, category_2]})
            
def test_suite():
    return unittest.makeSuite(DataFilesTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())