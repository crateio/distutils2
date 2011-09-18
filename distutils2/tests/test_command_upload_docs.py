"""Tests for distutils2.command.upload_docs."""
import os
import shutil
import zipfile
try:
    import _ssl
except ImportError:
    _ssl = None

from distutils2.command import upload_docs as upload_docs_mod
from distutils2.command.upload_docs import upload_docs, zip_dir
from distutils2.dist import Distribution
from distutils2.errors import PackagingFileError, PackagingOptionError

from distutils2.tests import unittest, support
try:
    import threading
    from distutils2.tests.pypi_server import PyPIServerTestCase
except ImportError:
    threading = None
    PyPIServerTestCase = unittest.TestCase


PYPIRC = """\
[distutils]
index-servers = server1

[server1]
repository = %s
username = real_slim_shady
password = long_island
"""


class UploadDocsTestCase(support.TempdirManager,
                         support.EnvironRestorer,
                         support.LoggingCatcher,
                         PyPIServerTestCase):

    restore_environ = ['HOME']

    def setUp(self):
        super(UploadDocsTestCase, self).setUp()
        self.tmp_dir = self.mkdtemp()
        self.rc = os.path.join(self.tmp_dir, '.pypirc')
        os.environ['HOME'] = self.tmp_dir
        self.dist = Distribution()
        self.dist.metadata['Name'] = "distr-name"
        self.cmd = upload_docs(self.dist)

    def test_default_uploaddir(self):
        sandbox = self.mkdtemp()
        previous = os.getcwd()
        os.chdir(sandbox)
        try:
            os.mkdir("build")
            self.prepare_sample_dir("build")
            self.cmd.ensure_finalized()
            self.assertEqual(self.cmd.upload_dir, os.path.join("build", "docs"))
        finally:
            os.chdir(previous)

    def test_default_uploaddir_looks_for_doc_also(self):
        sandbox = self.mkdtemp()
        previous = os.getcwd()
        os.chdir(sandbox)
        try:
            os.mkdir("build")
            self.prepare_sample_dir("build")
            os.rename(os.path.join("build", "docs"), os.path.join("build", "doc"))
            self.cmd.ensure_finalized()
            self.assertEqual(self.cmd.upload_dir, os.path.join("build", "doc"))
        finally:
            os.chdir(previous)

    def prepare_sample_dir(self, sample_dir=None):
        if sample_dir is None:
            sample_dir = self.mkdtemp()
        os.mkdir(os.path.join(sample_dir, "docs"))
        self.write_file(os.path.join(sample_dir, "docs", "index.html"), "Ce mortel ennui")
        self.write_file(os.path.join(sample_dir, "index.html"), "Oh la la")
        return sample_dir

    def test_zip_dir(self):
        source_dir = self.prepare_sample_dir()
        compressed = zip_dir(source_dir)

        zip_f = zipfile.ZipFile(compressed)
        self.assertEqual(zip_f.namelist(), ['index.html', 'docs/index.html'])

    def prepare_command(self):
        self.cmd.upload_dir = self.prepare_sample_dir()
        self.cmd.ensure_finalized()
        self.cmd.repository = self.pypi.full_address
        self.cmd.username = "username"
        self.cmd.password = "password"

    def test_upload(self):
        self.prepare_command()
        self.cmd.run()

        self.assertEqual(len(self.pypi.requests), 1)
        handler, request_data = self.pypi.requests[-1]
        self.assertIn("content", request_data)
        self.assertIn("Basic", handler.headers['authorization'])
        self.assertTrue(handler.headers['content-type']
            .startswith('multipart/form-data;'))

        action, name, version, content =\
            request_data.split("----------------GHSKFJDLGDS7543FJKLFHRE75642756743254".encode())[1:5]


        # check that we picked the right chunks
        self.assertIn('name=":action"', action)
        self.assertIn('name="name"', name)
        self.assertIn('name="version"', version)
        self.assertIn('name="content"', content)

        # check their contents
        self.assertIn('doc_upload', action)
        self.assertIn('distr-name', name)
        self.assertIn('docs/index.html', content)
        self.assertIn('Ce mortel ennui', content)

    @unittest.skipIf(_ssl is None, 'Needs SSL support')
    def test_https_connection(self):
        self.https_called = False

        orig_https = upload_docs_mod.httplib.HTTPSConnection

        def https_conn_wrapper(*args):
            self.https_called = True
            # the testing server is http
            return upload_docs_mod.httplib.HTTPConnection(*args)

        upload_docs_mod.httplib.HTTPSConnection = https_conn_wrapper
        try:
            self.prepare_command()
            self.cmd.run()
            self.assertFalse(self.https_called)

            self.cmd.repository = self.cmd.repository.replace("http", "https")
            self.cmd.run()
            self.assertTrue(self.https_called)
        finally:
            upload_docs_mod.httplib.HTTPSConnection = orig_https

    def test_handling_response(self):
        self.pypi.default_response_status = '403 Forbidden'
        self.prepare_command()
        self.cmd.run()
        self.assertIn('Upload failed (403): Forbidden', self.get_logs()[-1])

        self.pypi.default_response_status = '301 Moved Permanently'
        self.pypi.default_response_headers.append(("Location", "brand_new_location"))
        self.cmd.run()
        self.assertIn('brand_new_location', self.get_logs()[-1])

    def test_reads_pypirc_data(self):
        self.write_file(self.rc, PYPIRC % self.pypi.full_address)
        self.cmd.repository = self.pypi.full_address
        self.cmd.upload_dir = self.prepare_sample_dir()
        self.cmd.ensure_finalized()
        self.assertEqual(self.cmd.username, "real_slim_shady")
        self.assertEqual(self.cmd.password, "long_island")

    def test_checks_index_html_presence(self):
        self.cmd.upload_dir = self.prepare_sample_dir()
        os.remove(os.path.join(self.cmd.upload_dir, "index.html"))
        self.assertRaises(PackagingFileError, self.cmd.ensure_finalized)

    def test_checks_upload_dir(self):
        self.cmd.upload_dir = self.prepare_sample_dir()
        shutil.rmtree(os.path.join(self.cmd.upload_dir))
        self.assertRaises(PackagingOptionError, self.cmd.ensure_finalized)

    def test_show_response(self):
        self.prepare_command()
        self.cmd.show_response = True
        self.cmd.run()
        record = self.get_logs()[-1]
        self.assertTrue(record, "should report the response")
        self.assertIn(self.pypi.default_response_data, record)

UploadDocsTestCase = unittest.skipIf(threading is None, "Needs threading")(UploadDocsTestCase)
def test_suite():
    return unittest.makeSuite(UploadDocsTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
