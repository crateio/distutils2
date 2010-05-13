"""Tests for distutils.command.bdist."""
import unittest2, urllib, urllib2
from distutils2.tests.pypi_server import PyPIServer

class PyPIServerTest(unittest2.TestCase):

    def test_records_requests(self):
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

def test_suite():
    return unittest2.makeSuite(PyPIServerTest)

if __name__ == '__main__':
    unittest2.main(defaultTest="test_suite")
