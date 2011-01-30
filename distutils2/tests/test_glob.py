import os
import sys
import re
from StringIO import StringIO

from distutils2.tests import unittest, support, run_unittest
from distutils2.util import iglob, RICH_GLOB

class GlobTestCaseBase(support.TempdirManager,
                       support.LoggingCatcher,
                       unittest.TestCase):

    def build_files_tree(self, files):
        tempdir = self.mkdtemp()
        for filepath in files:
            is_dir = filepath.endswith('/')
            filepath = os.path.join(tempdir, *filepath.split('/'))
            if is_dir:
                dirname = filepath
            else:
                dirname = os.path.dirname(filepath)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)
            if not is_dir:
                self.write_file(filepath, 'babar')
        return tempdir

    @staticmethod
    def os_dependant_path(path):
        path = path.rstrip('/').split('/')
        return os.path.join(*path)

    def clean_tree(self, spec):
        files = []
        for path, includes in list(spec.items()):
            if includes:
                files.append(self.os_dependant_path(path))
        return files

class GlobTestCase(GlobTestCaseBase):


    def assertGlobMatch(self, glob, spec):
        """"""
        tempdir  = self.build_files_tree(spec)
        expected = self.clean_tree(spec)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(tempdir)
        result = list(iglob(glob))
        self.assertItemsEqual(expected, result)

    def test_regex_rich_glob(self):
        matches = RICH_GLOB.findall(r"babar aime les {fraises} est les {huitres}")
        self.assertEquals(["fraises","huitres"], matches)

    def test_simple_glob(self):
        glob = '*.tp?'
        spec  = {'coucou.tpl': True,
                 'coucou.tpj': True,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_simple_glob_in_dir(self):
        glob = 'babar/*.tp?'
        spec  = {'babar/coucou.tpl': True,
                 'babar/coucou.tpj': True,
                 'babar/toto.bin': False,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_recursive_glob_head(self):
        glob = '**/tip/*.t?l'
        spec  = {'babar/zaza/zuzu/tip/coucou.tpl': True,
                 'babar/z/tip/coucou.tpl': True,
                 'babar/tip/coucou.tpl': True,
                 'babar/zeop/tip/babar/babar.tpl': False,
                 'babar/z/tip/coucou.bin': False,
                 'babar/toto.bin': False,
                 'zozo/zuzu/tip/babar.tpl': True,
                 'zozo/tip/babar.tpl': True,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_recursive_glob_tail(self):
        glob = 'babar/**'
        spec = {'babar/zaza/': True,
                'babar/zaza/zuzu/': True,
                'babar/zaza/zuzu/babar.xml': True,
                'babar/zaza/zuzu/toto.xml': True,
                'babar/zaza/zuzu/toto.csv': True,
                'babar/zaza/coucou.tpl': True,
                'babar/bubu.tpl': True,
                'zozo/zuzu/tip/babar.tpl': False,
                'zozo/tip/babar.tpl': False,
                'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_recursive_glob_middle(self):
        glob = 'babar/**/tip/*.t?l'
        spec  = {'babar/zaza/zuzu/tip/coucou.tpl': True,
                 'babar/z/tip/coucou.tpl': True,
                 'babar/tip/coucou.tpl': True,
                 'babar/zeop/tip/babar/babar.tpl': False,
                 'babar/z/tip/coucou.bin': False,
                 'babar/toto.bin': False,
                 'zozo/zuzu/tip/babar.tpl': False,
                 'zozo/tip/babar.tpl': False,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_glob_set_tail(self):
        glob = 'bin/*.{bin,sh,exe}'
        spec  = {'bin/babar.bin': True,
                 'bin/zephir.sh': True,
                 'bin/celestine.exe': True,
                 'bin/cornelius.bat': False,
                 'bin/cornelius.xml': False,
                 'toto/yurg': False,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_glob_set_middle(self):
        glob = 'xml/{babar,toto}.xml'
        spec  = {'xml/babar.xml': True,
                 'xml/toto.xml': True,
                 'xml/babar.xslt': False,
                 'xml/cornelius.sgml': False,
                 'xml/zephir.xml': False,
                 'toto/yurg.xml': False,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_glob_set_head(self):
        glob = '{xml,xslt}/babar.*'
        spec  = {'xml/babar.xml': True,
                 'xml/toto.xml': False,
                 'xslt/babar.xslt': True,
                 'xslt/toto.xslt': False,
                 'toto/yurg.xml': False,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_glob_all(self):
        glob = '{xml/*,xslt/**}/babar.xml'
        spec  = {'xml/a/babar.xml': True,
                 'xml/b/babar.xml': True,
                 'xml/a/c/babar.xml': False,
                 'xslt/a/babar.xml': True,
                 'xslt/b/babar.xml': True,
                 'xslt/a/c/babar.xml': True,
                 'toto/yurg.xml': False,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)


def test_suite():
    return unittest.makeSuite(GlobTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
