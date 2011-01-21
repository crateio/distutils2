# -*- encoding: utf-8 -*-
"""Tests for distutils.config."""
import os
import sys
from StringIO import StringIO

from distutils2.tests import unittest, support, run_unittest


SETUP_CFG = """
[metadata]
name = RestingParrot
version = 0.6.4
author = Carl Meyer
author_email = carl@oddbird.net
maintainer = Éric Araujo
maintainer_email = merwok@netwok.org
summary = A sample project demonstrating distutils2 packaging
description-file = README
keywords = distutils2, packaging, sample project

classifier =
  Development Status :: 4 - Beta
  Environment :: Console (Text Based)
  Environment :: X11 Applications :: GTK; python_version < '3'
  License :: OSI Approved :: MIT License
  Programming Language :: Python
  Programming Language :: Python :: 2
  Programming Language :: Python :: 3

requires_python = >=2.4, <3.2

requires_dist =
  PetShoppe
  MichaelPalin (> 1.1)
  pywin32; sys.platform == 'win32'
  pysqlite2; python_version < '2.5'
  inotify (0.0.1); sys.platform == 'linux2'

requires_external = libxml2

provides_dist = distutils2-sample-project (0.2)
                unittest2-sample-project

project_url =
  Main repository, http://bitbucket.org/carljm/sample-distutils2-project
  Fork in progress, http://bitbucket.org/Merwok/sample-distutils2-project

[files]
packages = one
           src:two
           src2:three

modules = haven

scripts =
  script1.py
  scripts/find-coconuts
  bin/taunt

package_data =
  cheese = data/templates/*

data_files =
  bitmaps = bm/b1.gif, bm/b2.gif
  config = cfg/data.cfg
  /etc/init.d = init-script

# Replaces MANIFEST.in
sdist_extra =
  include THANKS HACKING
  recursive-include examples *.txt *.py
  prune examples/sample?/build

[global]
commands =
    distutils2.tests.test_config.FooBarBazTest

compilers =
    distutils2.tests.test_config.DCompiler

setup_hook = distutils2.tests.test_config.hook



[install_dist]
sub_commands = foo
"""


class DCompiler(object):
    name = 'd'
    description = 'D Compiler'

    def __init__(self, *args):
        pass

def hook(content):
    content['metadata']['version'] += '.dev1'


class FooBarBazTest(object):

    def __init__(self, dist):
        self.distribution = dist

    @classmethod
    def get_command_name(self):
        return 'foo'

    def run(self):
        self.distribution.foo_was_here = 1

    def nothing(self):
        pass

    def get_source_files(self):
        return []

    ensure_finalized = finalize_options = initialize_options = nothing


class ConfigTestCase(support.TempdirManager,
                     support.LoggingCatcher,
                     unittest.TestCase):

    def setUp(self):
        super(ConfigTestCase, self).setUp()
        self.addCleanup(setattr, sys, 'stdout', sys.stdout)
        self.addCleanup(setattr, sys, 'stderr', sys.stderr)
        self.addCleanup(os.chdir, os.getcwd())

    def test_config(self):
        tempdir = self.mkdtemp()
        os.chdir(tempdir)
        self.write_file('setup.cfg', SETUP_CFG)
        self.write_file('README', 'yeah')

        # try to load the metadata now
        sys.stdout = StringIO()
        sys.argv[:] = ['setup.py', '--version']
        old_sys = sys.argv[:]
        try:
            from distutils2.run import main
            dist = main()
        finally:
            sys.argv[:] = old_sys

        # sanity check
        self.assertEqual(sys.stdout.getvalue(), '0.6.4.dev1' + os.linesep)

        # check what was done
        self.assertEqual(dist.metadata['Author'], 'Carl Meyer')
        self.assertEqual(dist.metadata['Author-Email'], 'carl@oddbird.net')

        # the hook adds .dev1
        self.assertEqual(dist.metadata['Version'], '0.6.4.dev1')

        wanted = ['Development Status :: 4 - Beta',
                'Environment :: Console (Text Based)',
                "Environment :: X11 Applications :: GTK; python_version < '3'",
                'License :: OSI Approved :: MIT License',
                'Programming Language :: Python',
                'Programming Language :: Python :: 2',
                'Programming Language :: Python :: 3']
        self.assertEqual(dist.metadata['Classifier'], wanted)

        wanted = ['distutils2', 'packaging', 'sample project']
        self.assertEqual(dist.metadata['Keywords'], wanted)

        self.assertEqual(dist.metadata['Requires-Python'], '>=2.4, <3.2')

        wanted = ['PetShoppe',
                  'MichaelPalin (> 1.1)',
                  "pywin32; sys.platform == 'win32'",
                  "pysqlite2; python_version < '2.5'",
                  "inotify (0.0.1); sys.platform == 'linux2'"]

        self.assertEqual(dist.metadata['Requires-Dist'], wanted)
        urls = [('Main repository',
                 'http://bitbucket.org/carljm/sample-distutils2-project'),
                ('Fork in progress',
                 'http://bitbucket.org/Merwok/sample-distutils2-project')]
        self.assertEqual(dist.metadata['Project-Url'], urls)


        self.assertEqual(dist.packages, ['one', 'two', 'three'])
        self.assertEqual(dist.py_modules, ['haven'])
        self.assertEqual(dist.package_data, {'cheese': 'data/templates/*'})
        self.assertEqual(dist.data_files,
            [('bitmaps ', ['bm/b1.gif', 'bm/b2.gif']),
             ('config ', ['cfg/data.cfg']),
             ('/etc/init.d ', ['init-script'])])
        self.assertEqual(dist.package_dir['two'], 'src')

        # Make sure we get the foo command loaded.  We use a string comparison
        # instead of assertIsInstance because the class is not the same when
        # this test is run directly: foo is distutils2.tests.test_config.Foo
        # because get_command_class uses the full name, but a bare "Foo" in
        # this file would be __main__.Foo when run as "python test_config.py".
        # The name FooBarBazTest should be unique enough to prevent
        # collisions.
        self.assertEqual(dist.get_command_obj('foo').__class__.__name__,
                         'FooBarBazTest')

        # did the README got loaded ?
        self.assertEqual(dist.metadata['description'], 'yeah')

        # do we have the D Compiler enabled ?
        from distutils2.compiler import new_compiler, _COMPILERS
        self.assertIn('d', _COMPILERS)
        d = new_compiler(compiler='d')
        self.assertEqual(d.description, 'D Compiler')

    def test_sub_commands(self):
        tempdir = self.mkdtemp()
        os.chdir(tempdir)
        self.write_file('setup.cfg', SETUP_CFG)
        self.write_file('README', 'yeah')
        self.write_file('haven.py', '#')
        self.write_file('script1.py', '#')
        os.mkdir('scripts')
        self.write_file(os.path.join('scripts', 'find-coconuts'), '#')
        os.mkdir('bin')
        self.write_file(os.path.join('bin', 'taunt'), '#')

        for pkg in ('one', 'src', 'src2'):
            os.mkdir(pkg)
            self.write_file(os.path.join(pkg, '__init__.py'), '#')

        # try to run the install command to see if foo is called
        sys.stdout = sys.stderr = StringIO()
        sys.argv[:] = ['', 'install_dist']
        old_sys = sys.argv[:]
        try:
            from distutils2.run import main
            dist = main()
        finally:
            sys.argv[:] = old_sys

        self.assertEqual(dist.foo_was_here, 1)


def test_suite():
    return unittest.makeSuite(ConfigTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
