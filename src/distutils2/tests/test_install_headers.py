"""Tests for distutils.command.install_headers."""
import sys
import os
import getpass

from distutils2.command.install_headers import install_headers
from distutils2.tests import support
from distutils2.tests.support import unittest

class InstallHeadersTestCase(support.TempdirManager,
                             support.LoggingCatcher,
                             support.EnvironGuard,
                             unittest.TestCase):

    def test_simple_run(self):
        # we have two headers
        header_list = self.mkdtemp()
        header1 = os.path.join(header_list, 'header1')
        header2 = os.path.join(header_list, 'header2')
        self.write_file(header1)
        self.write_file(header2)
        headers = [header1, header2]

        pkg_dir, dist = self.create_dist(headers=headers)
        cmd = install_headers(dist)
        self.assertEqual(cmd.get_inputs(), headers)

        # let's run the command
        cmd.install_dir = os.path.join(pkg_dir, 'inst')
        cmd.ensure_finalized()
        cmd.run()

        # let's check the results
        self.assertEqual(len(cmd.get_outputs()), 2)

def test_suite():
    return unittest.makeSuite(InstallHeadersTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
