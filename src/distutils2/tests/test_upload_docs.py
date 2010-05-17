"""Tests for distutils.command.upload_docs."""
# -*- encoding: utf8 -*-
import httplib, os, os.path, tempfile, unittest2, zipfile
from cStringIO import StringIO

from distutils2.command import upload_docs as upload_docs_mod
from distutils2.command.upload_docs import (upload_docs, zip_dir,
                                    encode_multipart)
from distutils2.core import Distribution

from distutils2.errors import DistutilsFileError

from distutils2.tests import support
from distutils2.tests.pypi_server import PyPIServer, PyPIServerTestCase
from distutils2.tests.test_config import PyPIRCCommandTestCase


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

PYPIRC = """\
[distutils]
index-servers = server1

[server1]
repository = %s
username = real_slim_shady
password = long_island
"""

class UploadDocsTestCase(PyPIServerTestCase, PyPIRCCommandTestCase):

    def setUp(self):
        super(UploadDocsTestCase, self).setUp()
        self.dist = Distribution()
        self.dist.metadata['Name'] = "distr-name"
        self.cmd = upload_docs(self.dist)

    def test_generates_uploaddir_if_not_given(self):
        self.assertEqual(self.cmd.upload_dir, None)
        self.cmd.ensure_finalized()
        self.assertEqual(self.cmd.upload_dir, os.path.join("build", "docs"))

    def prepare_sample_dir(self):
        sample_dir = tempfile.mkdtemp()
        os.mkdir(os.path.join(sample_dir, "some_dir"))
        self.write_file(os.path.join(sample_dir, "some_dir", "index.html"), "Ce mortel ennui")
        self.write_file(os.path.join(sample_dir, "index.html"), "Oh la la")
        return sample_dir

    def test_zip_dir(self):
        source_dir = self.prepare_sample_dir()
        compressed = zip_dir(source_dir)

        zip_f = zipfile.ZipFile(compressed)
        self.assertEqual(zip_f.namelist(), ['index.html', 'some_dir/index.html'])

    def test_encode_multipart(self):
        fields = [("a", "b"), ("c", "d")]
        files = [("e", "f", "g"), ("h", "i", "j")]
        content_type, body = encode_multipart(fields, files, "-x")
        self.assertEqual(content_type, "multipart/form-data; boundary=-x")
        self.assertEqual(body, EXPECTED_MULTIPART_OUTPUT)

    def prepare_command(self):
        self.cmd.ensure_finalized()
        self.cmd.repository = self.pypi.full_address
        self.cmd.upload_dir = self.prepare_sample_dir()
        self.cmd.username = "username"
        self.cmd.password = "password"

    def test_upload(self):
        self.prepare_command()
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
        self.assertIn("some_dir/index.html", content)
        self.assertIn("Ce mortel ennui", content)

    def test_https_connection(self):
        https_called = False
        orig_https = upload_docs_mod.httplib.HTTPSConnection
        def https_conn_wrapper(*args):
            https_called = True
            return upload_docs_mod.httplib.HTTPConnection(*args) # the testing server is http
        upload_docs_mod.httplib.HTTPSConnection = https_conn_wrapper
        try:
            self.prepare_command()
            self.cmd.run()
            self.assertFalse(https_called)

            self.cmd.repository = self.cmd.repository.replace("http", "https")
            self.cmd.run()
            self.assertFalse(https_called)
        finally:
            upload_docs_mod.httplib.HTTPSConnection = orig_https

    def test_handling_response(self):
        calls = []
        def aggr(*args):
            calls.append(args)
        self.pypi.default_response_status = '403 Forbidden'
        self.prepare_command()
        self.cmd.announce = aggr
        self.cmd.run()
        message, _ = calls[-1]
        self.assertIn('Upload failed (403): Forbidden', message)

        calls = []
        self.pypi.default_response_status = '301 Moved Permanently'
        self.pypi.default_response_headers.append(("Location", "brand_new_location"))
        self.cmd.run()
        message, _ = calls[-1]
        self.assertIn('brand_new_location', message)

    def test_reads_pypirc_data(self):
        self.write_file(self.rc, PYPIRC % self.pypi.full_address)
        self.cmd.repository = self.pypi.full_address
        self.cmd.ensure_finalized()
        self.assertEqual(self.cmd.username, "real_slim_shady")
        self.assertEqual(self.cmd.password, "long_island")

    def test_checks_index_html_presence(self):
        self.prepare_command()
        os.remove(os.path.join(self.cmd.upload_dir, "index.html"))
        self.assertRaises(DistutilsFileError, self.cmd.run)

def test_suite():
    return unittest2.makeSuite(UploadDocsTestCase)

if __name__ == "__main__":
    unittest2.main(defaultTest="test_suite")
