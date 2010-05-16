import Queue, threading, time, unittest2
from wsgiref.simple_server import make_server

class PyPIServerTestCase(unittest2.TestCase):

    def setUp(self):
        super(PyPIServerTestCase, self).setUp()
        self.pypi = PyPIServer()
        self.pypi.start()

    def tearDown(self):
        super(PyPIServerTestCase, self).tearDown()
        self.pypi.stop()

class PyPIServer(threading.Thread):
    """Thread that wraps a wsgi app"""
    def __init__(self):
        threading.Thread.__init__(self)
        self.httpd = make_server('', 0, self.pypi_app)
        self.httpd.RequestHandlerClass.log_request = lambda *_: None
        self.address = self.httpd.server_address
        self.request_queue = Queue.Queue()
        self._requests = []
        self._default_response_status = "200 OK"
        self._default_response_headers = [('Content-type', 'text/plain')]
        self._default_response_data = ["hello"]

    def run(self):
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()
        self.join()

    def pypi_app(self, environ, start_response):
        # record the request
        if environ.get("CONTENT_LENGTH"):
            request_data = environ.pop('wsgi.input').read(int(environ['CONTENT_LENGTH']))
        else:
            request_data = environ.pop('wsgi.input').read()
        self.request_queue.put((environ, request_data))
        # send back a response
        status, headers, data = self.get_next_response()
        start_response(status, headers)
        return data

    def get_next_response(self):
        return (self._default_response_status,
                self._default_response_headers,
                self._default_response_data)

    @property
    def requests(self):
        while True:
            try:
                self._requests.append(self.request_queue.get_nowait())
            except Queue.Empty:
                break
        return self._requests

    @property
    def full_address(self):
        return "http://%s:%s" % self.address
