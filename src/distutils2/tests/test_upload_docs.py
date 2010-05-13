"""Tests for distutils.command.upload_docs."""
# -*- encoding: utf8 -*-
import os, os.path, unittest2

from distutils2.command.upload_docs import upload_docs
from distutils2.core import Distribution

from distutils2.tests.pypi_server import PyPIServer
from distutils2.tests.test_upload import PyPIServerTestCase
from distutils2.tests.test_config import PYPIRC, PyPIRCCommandTestCase


class UploadDocsTestCase(PyPIServerTestCase, PyPIRCCommandTestCase):

    def setUp(self):
        super(UploadDocsTestCase, self).setUp()
        self.dist = Distribution()
        self.cmd = upload_docs(self.dist)

    def test_generates_uploaddir_if_none(self):
        self.cmd.ensure_finalized()
        self.assertEqual(self.cmd.upload_dir, os.path.join("build", "docs"))

    def test_zip_dir(self):
        pass

    def test_upload(self):
        pass

def test_suite():
    return unittest2.makeSuite(UploadDocsTestCase)

if __name__ == "__main__":
    unittest2.main(defaultTest="test_suite")
