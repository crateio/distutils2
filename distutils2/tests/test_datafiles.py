# -*- encoding: utf-8 -*-
"""Tests for distutils.data."""
import os
import sys

from distutils2.tests import unittest, support, run_unittest
from distutils2.tests.test_glob import GlobTestCaseBase
from distutils2.datafiles import resources_dests



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
                 'Babarlikestrawberry': None}
        tempdir = self.build_files_tree(spec)
        self.assertRaises(NotImplementedError, resources_dests, tempdir, rules)

    def test_recursive_glob(self):
        rules = [('', '**/*.bin', '{binary}')]
        spec  = {'binary0.bin': '{binary}/binary0.bin',
                 'scripts/binary1.bin': '{binary}/scripts/binary1.bin',
                 'scripts/bin/binary2.bin': '{binary}/scripts/bin/binary2.bin',
                 'you/kill/pandabear.guy': None}
        self.assertRulesMatch(rules, spec)

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
        self.assertRulesMatch(rules, spec)

    def test_resource_open(self):
        from distutils2._backport.sysconfig import _SCHEMES as sysconfig_SCHEMES
        from distutils2._backport.sysconfig import _get_default_scheme
            #dirty but hit marmoute

        tempdir = self.mkdtemp()
        
        old_scheme = sysconfig_SCHEMES

        sysconfig_SCHEMES.set(_get_default_scheme(), 'config',
            tempdir)

        pkg_dir, dist = self.create_dist()
        dist_name = dist.metadata['name']

        test_path = os.path.join(pkg_dir, 'test.cfg')
        self.write_file(test_path, 'Config')
        dist.data_files = {test_path : '{config}/test.cfg'}

        cmd = install_dist(dist)
        cmd.install_dir = os.path.join(pkg_dir, 'inst')
        content = 'Config'        
        
        cmd.ensure_finalized()
        cmd.run()

        cfg_dest = os.path.join(tempdir, 'test.cfg')

        self.assertEqual(resource_path(dist_name, test_path), cfg_dest)
        self.assertRaises(KeyError, lambda: resource_path(dist_name, 'notexis'))

        self.assertEqual(resource_open(dist_name, test_path).read(), content)
        self.assertRaises(KeyError, lambda: resource_open(dist_name, 'notexis'))
        
        sysconfig_SCHEMES = old_scheme

def test_suite():
    return unittest.makeSuite(DataFilesTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
