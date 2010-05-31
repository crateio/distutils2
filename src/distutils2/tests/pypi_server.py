import Queue, threading, time, unittest2
from wsgiref.simple_server import make_server
import os.path

PYPI_HTML_BASE_PATH = os.path.dirname(os.path.abspath(__file__)) + "/pypiserver"

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
        self.default_response_status = "200 OK"
        self.default_response_headers = [('Content-type', 'text/plain')]
        self.default_response_data = ["hello"]

    def run(self):
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()
        self.join()

    def pypi_app(self, environ, start_response):
        # record the request. Read the input only on PUT or POST requests
        if environ["REQUEST_METHOD"] in ("PUT", "POST"):
            if environ.get("CONTENT_LENGTH"):
                request_data = environ.pop('wsgi.input').read(int(environ['CONTENT_LENGTH']))
            else:
                request_data = environ.pop('wsgi.input').read()
        elif environ["REQUEST_METHOD"] in ("GET", "DELETE"):
            request_data = ''
            
        self.request_queue.put((environ, request_data))
        
        relative_path = environ["PATH_INFO"].replace(self.full_address, '')
        
        # serve the content from local disc if we request /simple
        if relative_path.startswith("/simple/"):
            file_to_serve = relative_path.replace("/simple", PYPI_HTML_BASE_PATH)
            try:
                file = open(file_to_serve)
                data = file.read()
                start_response("200 OK", [('Content-type', 'text/plain')])
            except IOError:
                start_response("404 NOT FOUND", [('Content-type', 'text/plain')])
                data = "Not Found"
            return data

        # otherwise serve the content from default_response* parameters
        else:
            # send back a response
            status, headers, data = self.get_next_response()
            start_response(status, headers)
            return data

    def get_next_response(self):
        return (self.default_response_status,
                self.default_response_headers,
                self.default_response_data)

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
