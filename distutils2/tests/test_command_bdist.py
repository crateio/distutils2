"""Tests for distutils.command.bdist."""

from distutils2.tests import run_unittest

from distutils2.command.bdist import bdist, show_formats
from distutils2.tests import unittest, support, captured_stdout


class BuildTestCase(support.TempdirManager,
                    unittest.TestCase):

    def test_formats(self):

        # let's create a command and make sure
        # we can fix the format
        pkg_pth, dist = self.create_dist()
        cmd = bdist(dist)
        cmd.formats = ['msi']
        cmd.ensure_finalized()
        self.assertEqual(cmd.formats, ['msi'])

        # what format bdist offers ?
        # XXX an explicit list in bdist is
        # not the best way to  bdist_* commands
        # we should add a registry
        formats = ['zip', 'gztar', 'bztar', 'ztar', 'tar', 'wininst', 'msi']
        formats.sort()
        found = cmd.format_command.keys()
        found.sort()
        self.assertEqual(found, formats)

    def test_show_formats(self):
        __, stdout = captured_stdout(show_formats)

        # the output should be a header line + one line per format
        num_formats = len(bdist.format_commands)
        output = [line for line in stdout.split('\n')
                  if line.strip().startswith('--formats=')]
        self.assertEqual(len(output), num_formats)


def test_suite():
    return unittest.makeSuite(BuildTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
