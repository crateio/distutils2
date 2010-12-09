"""Tests for distutils.mkcfg."""
import os
import sys
import StringIO
from distutils2.tests import run_unittest, support, unittest
from distutils2.mkcfg import MainProgram
from distutils2.mkcfg import ask_yn, ask

class MkcfgTestCase(support.TempdirManager,
                    unittest.TestCase):

    def setUp(self):
        super(MkcfgTestCase, self).setUp()
        self._stdin = sys.stdin
        self._stdout = sys.stdout        
        sys.stdin = StringIO.StringIO()
        sys.stdout = StringIO.StringIO()
        
    def tearDown(self):
        super(MkcfgTestCase, self).tearDown()
        sys.stdin = self._stdin
        sys.stdout = self._stdout
        
    def test_ask_yn(self):        
        sys.stdin.write('y\n')
        sys.stdin.seek(0)
        self.assertEqual('y', ask_yn('is this a test'))

    def test_ask(self):
        sys.stdin.write('a\n')
        sys.stdin.write('b\n')
        sys.stdin.seek(0)
        self.assertEqual('a', ask('is this a test'))
        self.assertEqual('b', ask(str(range(0,70)), default='c', lengthy=True))

    def test_set_multi(self):
        main = MainProgram()
        sys.stdin.write('aaaaa\n')
        sys.stdin.seek(0)
        main.data['author'] = []
        main._set_multi('_set_multi test', 'author')
        self.assertEqual(['aaaaa'], main.data['author'])
        
    def test_find_files(self):
        # making sure we scan a project dir correctly
        main = MainProgram()

        # building the structure
        tempdir = self.mkdtemp()
        dirs = ['pkg1', 'data', 'pkg2', 'pkg2/sub']
        files = ['README', 'setup.cfg', 'foo.py',
                 'pkg1/__init__.py', 'pkg1/bar.py',
                 'data/data1', 'pkg2/__init__.py',
                 'pkg2/sub/__init__.py']

        for dir_ in dirs:
            os.mkdir(os.path.join(tempdir, dir_))

        for file_ in files:
            path = os.path.join(tempdir, file_)
            self.write_file(path, 'xxx')

        old_dir = os.getcwd()
        os.chdir(tempdir)
        try:
            main._find_files()
        finally:
            os.chdir(old_dir)

        # do we have what we want ?
        self.assertEqual(main.data['packages'], ['pkg1', 'pkg2', 'pkg2.sub'])
        self.assertEqual(main.data['modules'], ['foo'])
        self.assertEqual(set(main.data['extra_files']),
                         set(['setup.cfg', 'README', 'data/data1']))


def test_suite():
    return unittest.makeSuite(MkcfgTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
