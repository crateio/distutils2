# -*- encoding: utf-8 -*-
"""Tests for distutils.data."""
import pkgutil
import sys

from distutils2._backport.pkgutil import resource_open
from distutils2._backport.pkgutil import resource_path
from distutils2._backport.pkgutil import disable_cache
from distutils2._backport.pkgutil import enable_cache
from distutils2.command.install_dist import install_dist
from distutils2.resources import resources_dests
from distutils2.tests import run_unittest
from distutils2.tests import unittest
from distutils2.tests.test_util import GlobTestCaseBase
import os
import tempfile


class DataFilesTestCase(GlobTestCaseBase):

    def assertRulesMatch(self, rules, spec):
        tempdir = self.build_files_tree(spec)
        expected = self.clean_tree(spec)
        result = resources_dests(tempdir, rules)
        self.assertEquals(expected, result)

    def clean_tree(self, spec):
        files = {}
        for path, value in spec.items():
            if value is not None:
                path = self.os_dependant_path(path)
                files[path] = value
        return files

    def test_simple_glob(self):
        rules = [('', '*.tpl', '{data}')]
        spec  = {'coucou.tpl': '{data}/coucou.tpl',
            'Donotwant': None}
        self.assertRulesMatch(rules, spec)

    def test_multiple_match(self):
        rules = [('scripts', '*.bin', '{appdata}'),
            ('scripts', '*', '{appscript}')]
        spec  = {'scripts/script.bin': '{appscript}/script.bin',
            'Babarlikestrawberry': None}
        self.assertRulesMatch(rules, spec)

    def test_set_match(self):
        rules = [('scripts', '*.{bin,sh}', '{appscript}')]
        spec  = {'scripts/script.bin': '{appscript}/script.bin',
            'scripts/babar.sh':  '{appscript}/babar.sh',
            'Babarlikestrawberry': None}
        self.assertRulesMatch(rules, spec)

    def test_set_match_multiple(self):
        rules = [('scripts', 'script{s,}.{bin,sh}', '{appscript}')]
        spec  = {'scripts/scripts.bin': '{appscript}/scripts.bin',
            'scripts/script.sh':  '{appscript}/script.sh',
            'Babarlikestrawberry': None}
        self.assertRulesMatch(rules, spec)

    def test_set_match_exclude(self):
        rules = [('scripts', '*', '{appscript}'),
            ('', '**/*.sh', None)]
        spec  = {'scripts/scripts.bin': '{appscript}/scripts.bin',
            'scripts/script.sh':  None,
            'Babarlikestrawberry': None}
        self.assertRulesMatch(rules, spec)

    def test_glob_in_base(self):
        rules = [('scrip*', '*.bin', '{appscript}')]
        spec  = {'scripts/scripts.bin': '{appscript}/scripts.bin',
                 'scripouille/babar.bin': '{appscript}/babar.bin',
                 'scriptortu/lotus.bin': '{appscript}/lotus.bin',
                 'Babarlikestrawberry': None}
        self.assertRulesMatch(rules, spec)

    def test_recursive_glob(self):
        rules = [('', '**/*.bin', '{binary}')]
        spec  = {'binary0.bin': '{binary}/binary0.bin',
            'scripts/binary1.bin': '{binary}/scripts/binary1.bin',
            'scripts/bin/binary2.bin': '{binary}/scripts/bin/binary2.bin',
            'you/kill/pandabear.guy': None}
        self.assertRulesMatch(rules, spec)

    def test_final_exemple_glob(self):
        rules = [
            ('mailman/database/schemas/', '*', '{appdata}/schemas'),
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
        self.assertRulesMatch(rules, spec)

    def test_resource_open(self):


        #Create a fake-dist
        temp_site_packages = tempfile.mkdtemp()

        dist_name = 'test'
        dist_info = os.path.join(temp_site_packages, 'test-0.1.dist-info')
        os.mkdir(dist_info)

        metadata_path = os.path.join(dist_info, 'METADATA')
        resources_path = os.path.join(dist_info, 'RESOURCES')

        metadata_file = open(metadata_path, 'w')

        metadata_file.write(
"""Metadata-Version: 1.2
Name: test
Version: 0.1
Summary: test
Author: me
        """)

        metadata_file.close()

        test_path = 'test.cfg'

        _, test_resource_path = tempfile.mkstemp()

        test_resource_file = open(test_resource_path, 'w')

        content = 'Config'
        test_resource_file.write(content)
        test_resource_file.close()

        resources_file = open(resources_path, 'w')

        resources_file.write("""%s,%s""" % (test_path, test_resource_path))
        resources_file.close()

        #Add fake site-packages to sys.path to retrieve fake dist
        old_sys_path = sys.path
        sys.path.insert(0, temp_site_packages)

        #Force pkgutil to rescan the sys.path
        disable_cache()

        #Try to retrieve resources paths and files
        self.assertEqual(resource_path(dist_name, test_path), test_resource_path)
        self.assertRaises(KeyError, resource_path, dist_name, 'notexis')

        self.assertEqual(resource_open(dist_name, test_path).read(), content)
        self.assertRaises(KeyError, resource_open, dist_name, 'notexis')

        sys.path = old_sys_path

        enable_cache()

def test_suite():
    return unittest.makeSuite(DataFilesTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
