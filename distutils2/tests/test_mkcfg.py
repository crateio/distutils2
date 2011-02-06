# -*- coding: utf-8 -*-
"""Tests for distutils.mkcfg."""
import os
import sys
import StringIO
from textwrap import dedent

from distutils2.tests import run_unittest, support, unittest
from distutils2.mkcfg import MainProgram
from distutils2.mkcfg import ask_yn, ask, main


class MkcfgTestCase(support.TempdirManager,
                    unittest.TestCase):

    def setUp(self):
        super(MkcfgTestCase, self).setUp()
        self._stdin = sys.stdin
        self._stdout = sys.stdout
        sys.stdin = StringIO.StringIO()
        sys.stdout = StringIO.StringIO()
        self._cwd = os.getcwd()
        self.wdir = self.mkdtemp()
        os.chdir(self.wdir)

    def tearDown(self):
        super(MkcfgTestCase, self).tearDown()
        sys.stdin = self._stdin
        sys.stdout = self._stdout
        os.chdir(self._cwd)

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
        tempdir = self.wdir
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

        main._find_files()

        # do we have what we want ?
        self.assertEqual(main.data['packages'], ['pkg1', 'pkg2', 'pkg2.sub'])
        self.assertEqual(main.data['modules'], ['foo'])
        self.assertEqual(set(main.data['extra_files']),
                         set(['setup.cfg', 'README', 'data/data1']))

    def test_convert_setup_py_to_cfg(self):
        self.write_file((self.wdir, 'setup.py'),
                        dedent("""
        # -*- coding: utf-8 -*-
        from distutils.core import setup
        lg_dsc = '''My super Death-scription
        barbar is now on the public domain,
        ho, baby !'''
        setup(name='pyxfoil',
              version='0.2',
              description='Python bindings for the Xfoil engine',
              long_description = lg_dsc,
              maintainer='André Espaze',
              maintainer_email='andre.espaze@logilab.fr',
              url='http://www.python-science.org/project/pyxfoil',
              license='GPLv2',
              packages=['pyxfoil', 'babar', 'me'],
              data_files=[('share/doc/pyxfoil', ['README.rst']),
                          ('share/man', ['pyxfoil.1']),
                         ],
              py_modules = ['my_lib', 'mymodule'],
              package_dir = {'babar' : '',
                             'me' : 'Martinique/Lamentin',
                            },
              package_data = {'babar': ['Pom', 'Flora', 'Alexander'],
                              'me': ['dady', 'mumy', 'sys', 'bro'],
                              '':  ['setup.py', 'README'],
                              'pyxfoil' : ['fengine.so'],
                             },
              scripts = ['my_script', 'bin/run'],
              )
        """))
        sys.stdin.write('y\n')
        sys.stdin.seek(0)
        main()
        fp = open(os.path.join(self.wdir, 'setup.cfg'))
        try:
            lines = set([line.rstrip() for line in fp])
        finally:
            fp.close()
        self.assertEqual(lines, set(['',
            '[metadata]',
            'version = 0.2',
            'name = pyxfoil',
            'maintainer = André Espaze',
            'description = My super Death-scription',
            '       |barbar is now on the public domain,',
            '       |ho, baby !',
            'maintainer_email = andre.espaze@logilab.fr',
            'home_page = http://www.python-science.org/project/pyxfoil',
            'download_url = UNKNOWN',
            'summary = Python bindings for the Xfoil engine',
            '[files]',
            'modules = my_lib',
            '    mymodule',
            'packages = pyxfoil',
            '    babar',
            '    me',
            'extra_files = Martinique/Lamentin/dady',
            '    Martinique/Lamentin/mumy',
            '    Martinique/Lamentin/sys',
            '    Martinique/Lamentin/bro',
            '    Pom',
            '    Flora',
            '    Alexander',
            '    setup.py',
            '    README',
            '    pyxfoil/fengine.so',
            'scripts = my_script',
            '    bin/run',
            'resources =',
            '    README.rst = {doc}',
            '    pyxfoil.1 = {man}',
        ]))

    def test_convert_setup_py_to_cfg_with_description_in_readme(self):
        self.write_file((self.wdir, 'setup.py'),
                        dedent("""
        # -*- coding: utf-8 -*-
        from distutils.core import setup
        lg_dsc = open('README.txt').read()
        setup(name='pyxfoil',
              version='0.2',
              description='Python bindings for the Xfoil engine',
              long_description=lg_dsc,
              maintainer='André Espaze',
              maintainer_email='andre.espaze@logilab.fr',
              url='http://www.python-science.org/project/pyxfoil',
              license='GPLv2',
              packages=['pyxfoil'],
              package_data={'pyxfoil' : ['fengine.so', 'babar.so']},
              data_files=[
                ('share/doc/pyxfoil', ['README.rst']),
                ('share/man', ['pyxfoil.1']),
              ],
        )
        """))
        self.write_file((self.wdir, 'README.txt'),
                        dedent('''
My super Death-scription
barbar is now on the public domain,
ho, baby !
                        '''))
        sys.stdin.write('y\n')
        sys.stdin.seek(0)
        main()
        fp = open(os.path.join(self.wdir, 'setup.cfg'))
        try:
            lines = set([line.rstrip() for line in fp])
        finally:
            fp.close()
        self.assertEqual(lines, set(['',
            '[metadata]',
            'version = 0.2',
            'name = pyxfoil',
            'maintainer = André Espaze',
            'maintainer_email = andre.espaze@logilab.fr',
            'home_page = http://www.python-science.org/project/pyxfoil',
            'download_url = UNKNOWN',
            'summary = Python bindings for the Xfoil engine',
            'description-file = README.txt',
            '[files]',
            'packages = pyxfoil',
            'extra_files = pyxfoil/fengine.so',
            '    pyxfoil/babar.so',
            'resources =',
            '    README.rst = {doc}',
            '    pyxfoil.1 = {man}',
        ]))


def test_suite():
    return unittest.makeSuite(MkcfgTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
