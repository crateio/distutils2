"""Tests for distutils.command.upload_docs."""
# -*- encoding: utf8 -*-
import os, os.path, tempfile, unittest2, zipfile
from cStringIO import StringIO

from distutils2.command.upload_docs import (upload_docs, zip_dir,
                                    encode_multipart)
from distutils2.core import Distribution

from distutils2.tests import support
from distutils2.tests.pypi_server import PyPIServer
from distutils2.tests.test_upload import PyPIServerTestCase
from distutils2.tests.test_config import PYPIRC, PyPIRCCommandTestCase


EXPECTED_MULTIPART_OUTPUT = "\r\n".join([
'---x',
'Content-Disposition: form-data; name="a"',
'',
'b',
'---x',
'Content-Disposition: form-data; name="c"',
'',
'd',
'---x',
'Content-Disposition: form-data; name="e"; filename="f"',
'',
'g',
'---x',
'Content-Disposition: form-data; name="h"; filename="i"',
'',
'j',
'---x--',
'',
])

class UploadDocsTestCase(PyPIServerTestCase,
                         support.TempdirManager,
                         unittest2.TestCase):

    def setUp(self):
        super(UploadDocsTestCase, self).setUp()
        self.dist = Distribution()
        self.dist.metadata['Name'] = "distr-name"
        self.cmd = upload_docs(self.dist)

    def test_generates_uploaddir_name_not_given(self):
        self.cmd.ensure_finalized()
        self.assertEqual(self.cmd.upload_dir, os.path.join("build", "docs"))

    def prepare_sample_dir(self):
        sample_dir = tempfile.mkdtemp()
        os.mkdir(os.path.join(sample_dir, "some_dir"))
        some_file = open(os.path.join(sample_dir, "some_dir", "some_file"), "w")
        some_file.write("Ce mortel ennui")
        some_file.close()
        return sample_dir

    def test_zip_dir(self):
        source_dir = self.prepare_sample_dir()
        compressed = zip_dir(source_dir)

        zip_f = zipfile.ZipFile(compressed)
        self.assertEqual(zip_f.namelist(), ['some_dir/some_file'])

    def test_encode_multipart(self):
        fields = [("a", "b"), ("c", "d")]
        files = [("e", "f", "g"), ("h", "i", "j")]
        content_type, body = encode_multipart(fields, files, "-x")
        self.assertEqual(content_type, "multipart/form-data; boundary=-x")
        self.assertEqual(body, EXPECTED_MULTIPART_OUTPUT)

    def test_upload(self):
        self.cmd.ensure_finalized()
        self.cmd.repository = self.pypi.full_address
        self.cmd.upload_dir = self.prepare_sample_dir()
        self.cmd.username = "username"
        self.cmd.password = "password"
        self.cmd.run()

        self.assertEqual(len(self.pypi.requests), 1)
        environ, request_data = self.pypi.requests[-1]

        self.assertIn("content", request_data)
        self.assertIn("Basic", environ['HTTP_AUTHORIZATION'])
        self.assertTrue(environ['CONTENT_TYPE'].startswith('multipart/form-data;'))

        action, name, content =\
            request_data.split("----------------GHSKFJDLGDS7543FJKLFHRE75642756743254")[1:4]

        # check that we picked the right chunks
        self.assertIn('name=":action"', action)
        self.assertIn('name="name"', name)
        self.assertIn('name="content"', content)

        # check their contents
        self.assertIn("doc_upload", action)
        self.assertIn("distr-name", name)
        self.assertIn("some_dir/some_file", content)
        self.assertIn("Ce mortel ennui", content)

    def test_https_connection(self):
        pass

    def test_handling_response(self):
        pass

    def test_honours_dry_run(self):
        pass

def test_suite():
    return unittest2.makeSuite(UploadDocsTestCase)

if __name__ == "__main__":
    unittest2.main(defaultTest="test_suite")
