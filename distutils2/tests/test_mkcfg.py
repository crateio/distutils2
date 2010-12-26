"""Tests for distutils.mkcfg."""
import os
from distutils2.tests import run_unittest, support, unittest
from distutils2.mkcfg import MainProgram


class MkcfgTestCase(support.TempdirManager,
                    unittest.TestCase):

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
