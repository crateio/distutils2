"""Tests for distutils.command.build."""
import os
import sys

from distutils2.command.build import build
from distutils2._backport.sysconfig import get_platform
from distutils2.tests import unittest, support


class BuildTestCase(support.TempdirManager,
                    support.LoggingCatcher,
                    unittest.TestCase):

    def test_finalize_options(self):
        pkg_dir, dist = self.create_dist()
        cmd = build(dist)
        cmd.finalize_options()

        # if not specified, plat_name gets the current platform
        self.assertEqual(cmd.plat_name, get_platform())

        # build_purelib is build + lib
        wanted = os.path.join(cmd.build_base, 'lib')
        self.assertEqual(cmd.build_purelib, wanted)

        # build_platlib is 'build/lib.platform-x.x[-pydebug]'
        # examples:
        #   build/lib.macosx-10.3-i386-2.7
        plat_spec = '.%s-%s' % (cmd.plat_name, sys.version[0:3])
        if hasattr(sys, 'gettotalrefcount'):
            self.assertTrue(cmd.build_platlib.endswith('-pydebug'))
            plat_spec += '-pydebug'
        wanted = os.path.join(cmd.build_base, 'lib' + plat_spec)
        self.assertEqual(cmd.build_platlib, wanted)

        # by default, build_lib = build_purelib
        self.assertEqual(cmd.build_lib, cmd.build_purelib)

        # build_temp is build/temp.<plat>
        wanted = os.path.join(cmd.build_base, 'temp' + plat_spec)
        self.assertEqual(cmd.build_temp, wanted)

        # build_scripts is build/scripts-x.x
        wanted = os.path.join(cmd.build_base, 'scripts-' + sys.version[0:3])
        self.assertEqual(cmd.build_scripts, wanted)

        # executable is os.path.normpath(sys.executable)
        self.assertEqual(cmd.executable, os.path.normpath(sys.executable))


def test_suite():
    return unittest.makeSuite(BuildTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
