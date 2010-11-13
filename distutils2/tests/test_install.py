"""Tests for the distutils2.install module."""

import os
from tempfile import mkstemp

from distutils2 import install
from distutils2.index.xmlrpc import Client
from distutils2.metadata import DistributionMetadata
from distutils2.tests import run_unittest
from distutils2.tests.support import TempdirManager
from distutils2.tests.pypi_server import use_xmlrpc_server
from distutils2.tests.support import unittest


class InstalledDist(object):
    """Distribution object, represent distributions currently installed on the
    system"""
    def __init__(self, name, version, deps):
        self.name = name
        self.version = version
        self.metadata = DistributionMetadata()
        self.metadata['Requires-Dist'] = deps
        self.metadata['Provides-Dist'] = ['%s (%s)' % (name, version)]

    def __repr__(self):
        return '<InstalledDist %s>' % self.name


class ToInstallDist(object):
    """Distribution that will be installed"""

    def __init__(self, raise_error=False, files=False):
        self._raise_error = raise_error
        self._files = files
        self.install_called = False
        self.install_called_with = {}
        self.uninstall_called = False
        self._real_files = []
        if files:
            for f in range(0,3):
               self._real_files.append(mkstemp())

    def install(self, *args):
        self.install_called = True
        self.install_called_with = args
        if self._raise_error:
            raise Exception('Oops !')
        return ['/path/to/foo', '/path/to/bar']

    def uninstall(self, **args):
        self.uninstall_called = True

    def get_installed_files(self, **args):
        if self._files:
            return [f[1] for f in self._real_files]

    def get_install(self, **args):
        return self.get_installed_files()


def get_installed_dists(dists):
    objects = []
    for (name, version, deps) in dists:
        objects.append(InstalledDist(name, version, deps))
    return objects


class TestInstall(TempdirManager, unittest.TestCase):
    def _get_client(self, server, *args, **kwargs):
        return Client(server.full_address, *args, **kwargs)

    def _get_results(self, output):
        """return a list of results"""
        installed = [(o.name, '%s' % o.version) for o in output['install']]
        remove = [(o.name, '%s' % o.version) for o in output['remove']]
        conflict = [(o.name, '%s' % o.version) for o in output['conflict']]
        return (installed, remove, conflict)

    @use_xmlrpc_server()
    def test_existing_deps(self, server):
        # Test that the installer get the dependencies from the metadatas
        # and ask the index for this dependencies.
        # In this test case, we have choxie that is dependent from towel-stuff
        # 0.1, which is in-turn dependent on bacon <= 0.2:
        # choxie -> towel-stuff -> bacon.
        # Each release metadata is not provided in metadata 1.2.
        client = self._get_client(server)
        archive_path = '%s/distribution.tar.gz' % server.full_address
        server.xmlrpc.set_distributions([
            {'name':'choxie',
             'version': '2.0.0.9',
             'requires_dist': ['towel-stuff (0.1)',],
             'url': archive_path},
            {'name':'towel-stuff',
             'version': '0.1',
             'requires_dist': ['bacon (<= 0.2)',],
             'url': archive_path},
            {'name':'bacon',
             'version': '0.1',
             'requires_dist': [],
             'url': archive_path},
            ])
        installed = get_installed_dists([('bacon', '0.1', []),])
        output = install.get_infos("choxie", index=client,
                           installed=installed)

        # we dont have installed bacon as it's already installed on the system.
        self.assertEqual(0, len(output['remove']))
        self.assertEqual(2, len(output['install']))
        readable_output = [(o.name, '%s' % o.version)
                           for o in output['install']]
        self.assertIn(('towel-stuff', '0.1'), readable_output)
        self.assertIn(('choxie', '2.0.0.9'), readable_output)

    @use_xmlrpc_server()
    def test_upgrade_existing_deps(self, server):
        # Tests that the existing distributions can be upgraded if needed.
        client = self._get_client(server)
        archive_path = '%s/distribution.tar.gz' % server.full_address
        server.xmlrpc.set_distributions([
            {'name':'choxie',
             'version': '2.0.0.9',
             'requires_dist': ['towel-stuff (0.1)',],
             'url': archive_path},
            {'name':'towel-stuff',
             'version': '0.1',
             'requires_dist': ['bacon (>= 0.2)',],
             'url': archive_path},
            {'name':'bacon',
             'version': '0.2',
             'requires_dist': [],
             'url': archive_path},
            ])

        output = install.get_infos("choxie", index=client, installed=
                           get_installed_dists([('bacon', '0.1', []),]))
        installed = [(o.name, '%s' % o.version) for o in output['install']]

        # we need bacon 0.2, but 0.1 is installed.
        # So we expect to remove 0.1 and to install 0.2 instead.
        remove = [(o.name, '%s' % o.version) for o in output['remove']]
        self.assertIn(('choxie', '2.0.0.9'), installed)
        self.assertIn(('towel-stuff', '0.1'), installed)
        self.assertIn(('bacon', '0.2'), installed)
        self.assertIn(('bacon', '0.1'), remove)
        self.assertEqual(0, len(output['conflict']))

    @use_xmlrpc_server()
    def test_conflicts(self, server):
        # Tests that conflicts are detected
        client = self._get_client(server)
        archive_path = '%s/distribution.tar.gz' % server.full_address
        server.xmlrpc.set_distributions([
            {'name':'choxie',
             'version': '2.0.0.9',
             'requires_dist': ['towel-stuff (0.1)',],
             'url': archive_path},
            {'name':'towel-stuff',
             'version': '0.1',
             'requires_dist': ['bacon (>= 0.2)',],
             'url': archive_path},
            {'name':'bacon',
             'version': '0.2',
             'requires_dist': [],
             'url': archive_path},
            ])
        already_installed = [('bacon', '0.1', []),
                             ('chicken', '1.1', ['bacon (0.1)'])]
        output = install.get_infos("choxie", index=client, installed=
                           get_installed_dists(already_installed))

        # we need bacon 0.2, but 0.1 is installed.
        # So we expect to remove 0.1 and to install 0.2 instead.
        installed, remove, conflict = self._get_results(output)
        self.assertIn(('choxie', '2.0.0.9'), installed)
        self.assertIn(('towel-stuff', '0.1'), installed)
        self.assertIn(('bacon', '0.2'), installed)
        self.assertIn(('bacon', '0.1'), remove)
        self.assertIn(('chicken', '1.1'), conflict)

    @use_xmlrpc_server()
    def test_installation_unexisting_project(self, server):
        # Test that the isntalled raises an exception if the project does not
        # exists.
        client = self._get_client(server)
        self.assertRaises(install.InstallationException,
                          install.get_infos,
                          'unexistant project', index=client)

    def test_move_files(self):
        # test that the files are really moved, and that the new path is
        # returned.
        path = self.mkdtemp()
        newpath = self.mkdtemp()
        files = [os.path.join(path, '%s' % x) for x in range(1, 20)]
        for f in files:
            file(f, 'a+')
        output = [o for o in install.move_files(files, newpath)]

        # check that output return the list of old/new places
        for f in files:
            self.assertIn((f, '%s%s' % (newpath, f)), output)

        # remove the files
        for f in [o[1] for o in output]:  # o[1] is the new place
            os.remove(f)

    def test_update_infos(self):
        tests = [[{'foo': ['foobar', 'foo', 'baz'], 'baz': ['foo', 'foo']},
                  {'foo': ['additional_content', 'yeah'],
                   'baz': ['test', 'foo']},
                  {'foo': ['foobar', 'foo', 'baz', 'additional_content', 'yeah'],
                   'baz': ['foo', 'foo', 'test', 'foo']}],]

        for dict1, dict2, expect in tests:
            install._update_infos(dict1, dict2)
            for key in expect.keys():
                self.assertEqual(expect[key], dict1[key])

    def test_install_dists_rollback(self):
        # if one of the distribution installation fails, call uninstall on all
        # installed distributions.

        d1 = ToInstallDist()
        d2 = ToInstallDist(raise_error=True)
        self.assertRaises(Exception, install.install_dists, [d1, d2])
        for dist in (d1, d2):
            self.assertTrue(dist.install_called)
        self.assertTrue(d1.uninstall_called)
        self.assertFalse(d2.uninstall_called)

    def test_install_dists_success(self):
        # test that the install method is called on each of the distributions.
        d1 = ToInstallDist()
        d2 = ToInstallDist()
        install.install_dists([d1, d2])
        for dist in (d1, d2):
            self.assertTrue(dist.install_called)
        self.assertFalse(d1.uninstall_called)
        self.assertFalse(d2.uninstall_called)

    def test_install_from_infos_conflict(self):
        # assert conflicts raise an exception
        self.assertRaises(install.InstallationConflict,
            install.install_from_infos,
            conflicts=[ToInstallDist()])

    def test_install_from_infos_remove_success(self):
        old_install_dists = install.install_dists
        install.install_dists = lambda x,y=None: None
        try:
            dists = []
            for i in range(0,2):
                dists.append(ToInstallDist(files=True))
            install.install_from_infos(remove=dists)

            # assert that the files have been removed
            for dist in dists:
                for f in dist.get_installed_files():
                    self.assertFalse(os.path.exists(f))
        finally:
            install.install_dists = old_install_dists

    def test_install_from_infos_remove_rollback(self):
        # assert that if an error occurs, the removed files are restored.
        remove = []
        for i in range(0,2):
            remove.append(ToInstallDist(files=True, raise_error=True))
        to_install = [ToInstallDist(raise_error=True),
                   ToInstallDist()]

        install.install_from_infos(remove=remove, install=to_install)
        # assert that the files are in the same place
        # assert that the files have been removed
        for dist in remove:
            for f in dist.get_installed_files():
                self.assertTrue(os.path.exists(f))

    def test_install_from_infos_install_succes(self):
        # assert that the distribution can be installed
        install_path = "my_install_path"
        to_install = [ToInstallDist(), ToInstallDist()]

        install.install_from_infos(install=to_install,
                                         install_path=install_path)
        for dist in to_install:
            self.assertEquals(dist.install_called_with, (install_path,))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestInstall))
    return suite

if __name__ == '__main__':
    run_unittest(test_suite())
