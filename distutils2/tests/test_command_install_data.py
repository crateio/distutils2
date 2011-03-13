"""Tests for distutils.command.install_data."""
import cmd
import os

from distutils2.command.install_data import install_data
from distutils2.tests import unittest, support

class InstallDataTestCase(support.TempdirManager,
                          support.LoggingCatcher,
                          support.EnvironGuard,
                          unittest.TestCase):

    def test_simple_run(self):
        from distutils2._backport.sysconfig import _SCHEMES as sysconfig_SCHEMES
        from distutils2._backport.sysconfig import _get_default_scheme
            #dirty but hit marmoute

        old_scheme = sysconfig_SCHEMES

        pkg_dir, dist = self.create_dist()
        cmd = install_data(dist)
        cmd.install_dir = inst = os.path.join(pkg_dir, 'inst')

        sysconfig_SCHEMES.set(_get_default_scheme(), 'inst',
            os.path.join(pkg_dir, 'inst'))
        sysconfig_SCHEMES.set(_get_default_scheme(), 'inst2',
            os.path.join(pkg_dir, 'inst2'))

        one = os.path.join(pkg_dir, 'one')
        self.write_file(one, 'xxx')
        inst2 = os.path.join(pkg_dir, 'inst2')
        two = os.path.join(pkg_dir, 'two')
        self.write_file(two, 'xxx')

        cmd.data_files = {one : '{inst}/one', two : '{inst2}/two'}
        self.assertItemsEqual(cmd.get_inputs(), [one, two])

        # let's run the command
        cmd.ensure_finalized()
        cmd.run()

        # let's check the result
        self.assertEqual(len(cmd.get_outputs()), 2)
        rtwo = os.path.split(two)[-1]
        self.assertTrue(os.path.exists(os.path.join(inst2, rtwo)))
        rone = os.path.split(one)[-1]
        self.assertTrue(os.path.exists(os.path.join(inst, rone)))
        cmd.outfiles = []

        # let's try with warn_dir one
        cmd.warn_dir = 1
        cmd.ensure_finalized()
        cmd.run()

        # let's check the result
        self.assertEqual(len(cmd.get_outputs()), 2)
        self.assertTrue(os.path.exists(os.path.join(inst2, rtwo)))
        self.assertTrue(os.path.exists(os.path.join(inst, rone)))
        cmd.outfiles = []

        # now using root and empty dir
        cmd.root = os.path.join(pkg_dir, 'root')
        inst4 = os.path.join(pkg_dir, 'inst4')
        three = os.path.join(cmd.install_dir, 'three')
        self.write_file(three, 'xx')

        sysconfig_SCHEMES.set(_get_default_scheme(), 'inst3', cmd.install_dir)

        cmd.data_files = {one : '{inst}/one',
                          two : '{inst2}/two',
                          three : '{inst3}/three'}
        cmd.ensure_finalized()
        cmd.run()

        # let's check the result
        self.assertEqual(len(cmd.get_outputs()), 3)
        self.assertTrue(os.path.exists(os.path.join(inst2, rtwo)))
        self.assertTrue(os.path.exists(os.path.join(inst, rone)))

        sysconfig_SCHEMES = old_scheme

def test_suite():
    return unittest.makeSuite(InstallDataTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
