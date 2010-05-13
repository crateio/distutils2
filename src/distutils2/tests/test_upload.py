"""Tests for distutils.command.upload."""
# -*- encoding: utf8 -*-
import os, unittest2

from distutils2.command.upload import upload
from distutils2.core import Distribution

from distutils2.tests.pypi_server import PyPIServer
from distutils2.tests.test_config import PYPIRC, PyPIRCCommandTestCase


PYPIRC_NOPASSWORD = """\
[distutils]

index-servers =
    server1

[server1]
username:me
"""

class UploadTestCase(PyPIRCCommandTestCase):

    def setUp(self):
        super(UploadTestCase, self).setUp()
        assert not hasattr(self, "pypi")
        self.pypi = PyPIServer()
        self.pypi.start()

    def tearDown(self):
        self.pypi.stop()

    def test_finalize_options(self):
        # new format
        self.write_file(self.rc, PYPIRC)
        dist = Distribution()
        cmd = upload(dist)
        cmd.finalize_options()
        for attr, waited in (('username', 'me'), ('password', 'secret'),
                             ('realm', 'pypi'),
                             ('repository', 'http://pypi.python.org/pypi')):
            self.assertEquals(getattr(cmd, attr), waited)

    def test_saved_password(self):
        # file with no password
        self.write_file(self.rc, PYPIRC_NOPASSWORD)

        # make sure it passes
        dist = Distribution()
        cmd = upload(dist)
        cmd.ensure_finalized()
        self.assertEquals(cmd.password, None)

        # make sure we get it as well, if another command
        # initialized it at the dist level
        dist.password = 'xxx'
        cmd = upload(dist)
        cmd.finalize_options()
        self.assertEquals(cmd.password, 'xxx')

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
        environ, request_data = self.pypi.requests[-1]
        self.assertIn('dédé', request_data)
        self.assertIn('xxx', request_data)
        self.assert_(environ['CONTENT_LENGTH'] > 2000)
        self.assertTrue(environ['CONTENT_TYPE'].startswith('multipart/form-data'))
        self.assertEquals(environ['REQUEST_METHOD'], 'POST')
        self.assertNotIn('\n', environ['HTTP_AUTHORIZATION'])

def test_suite():
    return unittest2.makeSuite(UploadTestCase)

if __name__ == "__main__":
    unittest2.main(defaultTest="test_suite")
