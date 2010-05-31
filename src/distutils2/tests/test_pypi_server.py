"""Tests for distutils.command.bdist."""
import unittest2, urllib, urllib2
from distutils2.tests.pypi_server import PyPIServer

class PyPIServerTest(unittest2.TestCase):

    def test_records_requests(self):
        """We expect that PyPIServer can log our requests"""
        server = PyPIServer()
        server.start()
        self.assertEqual(len(server.requests), 0)

        data = "Rock Around The Bunker"
        headers = {"X-test-header": "Mister Iceberg"}

        request = urllib2.Request(server.full_address, data, headers)
        urllib2.urlopen(request)
        self.assertEqual(len(server.requests), 1)
        environ, request_data = server.requests[-1]
        self.assertIn("Rock Around The Bunker", request_data)
        self.assertEqual(environ["HTTP_X_TEST_HEADER"], "Mister Iceberg")
        server.stop()

    def test_serve_static_content(self):
        """We expect that when accessing the test PyPI server, files can 
        be served statically."""
        server = PyPIServer()
        server.start()
        
        # the file does not exists on the disc, so it might not be served
        url = server.full_address + "/simple/unexisting_page"
        request = urllib2.Request(url)
        try:
            urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            self.assertEqual(e.getcode(), 404)

        # now try serving a content that do exists
        url = server.full_address + "/simple/index.html"
        request = urllib2.Request(url)
        f = urllib2.urlopen(request)
        self.assertEqual(f.read(), "Yeah\n")

def test_suite():
    return unittest2.makeSuite(PyPIServerTest)

if __name__ == '__main__':
    unittest2.main(defaultTest="test_suite")
