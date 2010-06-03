"""Mocked PyPI Server implementation, to use in tests.

This module also provides a simple test case to extend if you need to use
the PyPIServer all along your test case. Be sure to read the documentation 
before any use.
"""

import Queue
import threading
import time
import unittest2
import urllib2
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from wsgiref.simple_server import make_server
import os.path

PYPI_DEFAULT_STATIC_PATH = os.path.dirname(os.path.abspath(__file__)) + "/pypiserver"

def use_pypi_server(*server_args, **server_kwargs):
    """Decorator to make use of the PyPIServer for test methods, 
    just when needed, and not for the entire duration of the testcase.
    """
    def wrapper(func):
        def wrapped(*args, **kwargs):
            server = PyPIServer(*server_args, **server_kwargs)
            server.start()
            func(server=server, *args, **kwargs)
            server.stop()
        return wrapped
    return wrapper 

class PyPIServerTestCase(unittest2.TestCase):

    def setUp(self):
        super(PyPIServerTestCase, self).setUp()
        self.pypi = PyPIServer()
        self.pypi.start()

    def tearDown(self):
        super(PyPIServerTestCase, self).tearDown()
        self.pypi.stop()

class PyPIServer(threading.Thread):
    """PyPI Mocked server.
    Provides a mocked version of the PyPI API's, to ease tests.

    Support serving static content and serving previously given text.
    """

    def __init__(self, test_static_path=None,
            static_filesystem_paths=["default"], static_uri_paths=["simple"]):
        """Initialize the server.

        static_uri_paths and static_base_path are parameters used to provides
        respectively the http_paths to serve statically, and where to find the
        matching files on the filesystem.
        """
        threading.Thread.__init__(self)
        self._run = True
        self.httpd = HTTPServer(('', 0), PyPIRequestHandler) 
        self.httpd.RequestHandlerClass.log_request = lambda *_: None
        self.httpd.RequestHandlerClass.pypi_server = self
        self.address = self.httpd.server_address
        self.request_queue = Queue.Queue()
        self._requests = []
        self.default_response_status = 200
        self.default_response_headers = [('Content-type', 'text/plain')]
        self.default_response_data = "hello"
        
        # initialize static paths / filesystems
        self.static_uri_paths = static_uri_paths
        if test_static_path is not None:
            static_filesystem_paths.append(test_static_path)
        self.static_filesystem_paths = [PYPI_DEFAULT_STATIC_PATH + "/" + path
            for path in static_filesystem_paths]

    def run(self):
        # loop because we can't stop it otherwise, for python < 2.6
        while True:
            self.httpd.handle_request()
            if not self._run:
                break

    def stop(self):
        """self shutdown is not supported for python < 2.6"""
        self._run = False

    def get_next_response(self):
        return (self.default_response_status,
                self.default_response_headers,
                self.default_response_data)

    @property
    def requests(self):
        """Use this property to get all requests that have been made
        to the server
        """
        while True:
            try:
                self._requests.append(self.request_queue.get_nowait())
            except Queue.Empty:
                break
        return self._requests

    @property
    def full_address(self):
        return "http://%s:%s" % self.address


class PyPIRequestHandler(SimpleHTTPRequestHandler):
    # we need to access the pypi server while serving the content
    pypi_server = None

    def do_POST(self):
        return self.serve_request()
    def do_GET(self):
        return self.serve_request()
    def do_DELETE(self):
        return self.serve_request()
    def do_PUT(self):
        return self.serve_request()

    def serve_request(self):
        """Serve the content.

        Also record the requests to be accessed later. If trying to access an
        url matching a static uri, serve static content, otherwise serve
        what is provided by the `get_next_response` method.
        """
        # record the request. Read the input only on PUT or POST requests
        if self.command in ("PUT", "POST"):
            if self.headers.dict.has_key("content-length"):
                request_data = self.rfile.read(
                    int(self.headers['content-length']))
            else:
                request_data = self.rfile.read()
        elif self.command in ("GET", "DELETE"):
            request_data = ''

        self.pypi_server.request_queue.put((self, request_data))

        # serve the content from local disc if we request an URL beginning
        # by a pattern defined in `static_paths`
        url_parts = self.path.split("/")
        if (len(url_parts) > 1 and 
                url_parts[1] in self.pypi_server.static_uri_paths):
            data = None
            # always take the last first.
            fs_paths = []
            fs_paths.extend(self.pypi_server.static_filesystem_paths)
            fs_paths.reverse()
            relative_path = self.path
            for fs_path in fs_paths:
                try:
                    if self.path.endswith("/"):
                        relative_path += "index.html"
                    file = open(fs_path + relative_path)
                    data = file.read()
                    self.make_response(data)
                except IOError:
                    pass

            if data is None:
                self.make_response("Not found", 404)

        # otherwise serve the content from get_next_response
        else:
            # send back a response
            status, headers, data = self.pypi_server.get_next_response()
            self.make_response(data, status, headers)

    def make_response(self, data, status=200, 
            headers=[('Content-type', 'text/html')]):
        """Send the response to the HTTP client"""
        if not isinstance(status, int):
            try:
                status = int(status)
            except ValueError:
                # we probably got something like YYY Codename. 
                # Just get the first 3 digits
                status = int(status[:3]) 

        self.send_response(status)
        for header, value in headers:
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(data)
