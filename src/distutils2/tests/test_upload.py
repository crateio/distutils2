"""Tests for distutils.command.upload."""
# -*- encoding: utf8 -*-
import os
import sys

from distutils2.command.upload import upload
from distutils2.core import Distribution

from distutils2.tests import support
from distutils2.tests.pypi_server import PyPIServer, PyPIServerTestCase
from distutils2.tests.support import unittest
from distutils2.tests.test_config import PYPIRC, PyPIRCCommandTestCase


PYPIRC_NOPASSWORD = """\
[distutils]

index-servers =
    server1

[server1]
username:me
"""

class UploadTestCase(PyPIServerTestCase, PyPIRCCommandTestCase):

    def test_finalize_options(self):
        # new format
        self.write_file(self.rc, PYPIRC)
        dist = Distribution()
        cmd = upload(dist)
        cmd.finalize_options()
        for attr, expected in (('username', 'me'), ('password', 'secret'),
                               ('realm', 'pypi'),
                               ('repository', 'http://pypi.python.org/pypi')):
            self.assertEqual(getattr(cmd, attr), expected)

    def test_saved_password(self):
        # file with no password
        self.write_file(self.rc, PYPIRC_NOPASSWORD)

        # make sure it passes
        dist = Distribution()
        cmd = upload(dist)
        cmd.ensure_finalized()
        self.assertEqual(cmd.password, None)

        # make sure we get it as well, if another command
        # initialized it at the dist level
        dist.password = 'xxx'
        cmd = upload(dist)
        cmd.finalize_options()
        self.assertEqual(cmd.password, 'xxx')

    def test_upload(self):
        path = os.path.join(self.tmp_dir, 'xxx')
        self.write_file(path)
        command, pyversion, filename = 'xxx', '2.6', path
        dist_files = [(command, pyversion, filename)]

        # lets run it
        pkg_dir, dist = self.create_dist(dist_files=dist_files, author=u'dédé')
        cmd = upload(dist)
        cmd.ensure_finalized()
        cmd.repository = self.pypi.full_address
        cmd.run()

        # what did we send ?
        handler, request_data = self.pypi.requests[-1]
        headers = handler.headers.dict
        self.assertIn('dédé', request_data)
        self.assertIn('xxx', request_data)
        self.assertEqual(int(headers['content-length']), len(request_data))
        self.assertTrue(int(headers['content-length']) < 2000)
        self.assertTrue(headers['content-type'].startswith('multipart/form-data'))
        self.assertEqual(handler.command, 'POST')
        self.assertNotIn('\n', headers['authorization'])

def test_suite():
    return unittest.makeSuite(UploadTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
