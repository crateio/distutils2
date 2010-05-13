"""Tests for distutils.command.upload_docs."""
# -*- encoding: utf8 -*-
import os, os.path, tempfile, unittest2, zipfile

from distutils2.command.upload_docs import upload_docs, zip_dir_into
from distutils2.core import Distribution

from distutils2.tests import support
from distutils2.tests.pypi_server import PyPIServer
from distutils2.tests.test_upload import PyPIServerTestCase
from distutils2.tests.test_config import PYPIRC, PyPIRCCommandTestCase


class UploadDocsTestCase(PyPIServerTestCase,
                         support.TempdirManager,
                         unittest2.TestCase):

    def setUp(self):
        super(UploadDocsTestCase, self).setUp()
        self.dist = Distribution()
        self.cmd = upload_docs(self.dist)

    def test_generates_uploaddir_name_not_given(self):
        self.cmd.ensure_finalized()
        self.assertEqual(self.cmd.upload_dir, os.path.join("build", "docs"))

    def test_zip_dir_into(self):
        source_dir = tempfile.mkdtemp()
        os.mkdir(os.path.join(source_dir, "some_dir"))
        some_file = open(os.path.join(source_dir, "some_dir", "some_file"), "w")
        some_file.write("Ce mortel ennui")
        some_file.close()
        dest_dir = tempfile.mkdtemp()
        destination = os.path.join(dest_dir, "archive.zip")
        zip_dir_into(source_dir, destination)

        self.assertTrue(zipfile.is_zipfile(destination))
        zip_f = zipfile.ZipFile(destination)
        self.assertEqual(zip_f.namelist(), ['some_dir/some_file'])

    def test_zip_dir(self):
        pass

    def test_upload(self):
        pass

    def test_honours_dry_run(self):
        pass

def test_suite():
    return unittest2.makeSuite(UploadDocsTestCase)

if __name__ == "__main__":
    unittest2.main(defaultTest="test_suite")
