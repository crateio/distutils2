"""Tests for the uninstall command."""
import os
import sys
from StringIO import StringIO
from distutils2._backport.pkgutil import disable_cache, enable_cache
from distutils2.tests import unittest, support, run_unittest
from distutils2.errors import DistutilsError
from distutils2.install import remove

SETUP_CFG = """
[metadata]
name = %(name)s
version = %(version)s

[files]
packages =
    %(name)s
    %(name)s.sub
"""

class UninstallTestCase(support.TempdirManager,
                     support.LoggingCatcher,
                     unittest.TestCase):

    def setUp(self):
        super(UninstallTestCase, self).setUp()
        self.addCleanup(setattr, sys, 'stdout', sys.stdout)
        self.addCleanup(setattr, sys, 'stderr', sys.stderr)
        self.addCleanup(os.chdir, os.getcwd())
        self.addCleanup(enable_cache)
        self.root_dir = self.mkdtemp()
        disable_cache()

    def run_setup(self, *args):
        # run setup with args
        args = ['', 'run'] + list(args)
        from distutils2.run import main
        dist = main(args)
        return dist

    def get_path(self, dist, name):
        from distutils2.command.install_dist import install_dist
        cmd = install_dist(dist)
        cmd.prefix = self.root_dir
        cmd.finalize_options()
        return getattr(cmd, 'install_'+name)

    def make_dist(self, pkg_name='foo', **kw):
        dirname = self.mkdtemp()
        kw['name'] = pkg_name
        if 'version' not in kw:
            kw['version'] = '0.1'
        self.write_file((dirname, 'setup.cfg'), SETUP_CFG % kw)
        os.mkdir(os.path.join(dirname, pkg_name))
        self.write_file((dirname, '__init__.py'), '#')
        self.write_file((dirname, pkg_name+'_utils.py'), '#')
        os.mkdir(os.path.join(dirname, pkg_name, 'sub'))
        self.write_file((dirname, pkg_name, 'sub', '__init__.py'), '#')
        self.write_file((dirname, pkg_name, 'sub', pkg_name+'_utils.py'), '#')
        return dirname

    def install_dist(self, pkg_name='foo', dirname=None, **kw):
        if not dirname:
            dirname = self.make_dist(pkg_name, **kw)
        os.chdir(dirname)
        dist = self.run_setup('install_dist', '--prefix='+self.root_dir)
        install_lib = self.get_path(dist, 'purelib')
        return dist, install_lib

    def test_uninstall_unknow_distribution(self):
        self.assertRaises(DistutilsError, remove, 'foo', paths=[self.root_dir])

    def test_uninstall(self):
        dist, install_lib = self.install_dist()
        self.assertIsFile(install_lib, 'foo', 'sub', '__init__.py')
        self.assertIsFile(install_lib, 'foo-0.1.dist-info', 'RECORD')
        remove('foo', paths=[install_lib])
        self.assertIsNotFile(install_lib, 'foo', 'sub', '__init__.py')
        self.assertIsNotFile(install_lib, 'foo-0.1.dist-info', 'RECORD')




def test_suite():
    return unittest.makeSuite(UninstallTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
