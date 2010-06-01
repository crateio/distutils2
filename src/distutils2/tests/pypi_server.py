import Queue, threading, time, unittest2
from wsgiref.simple_server import make_server
import os.path

PYPI_DEFAULT_STATIC_PATH =  os.path.dirname(os.path.abspath(__file__)) + "/pypiserver"

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
    
    def __init__(self, static_uri_paths=["pypi"],
            static_filesystem_paths=["default"]):
        """Initialize the server.

        static_uri_paths and static_base_path are parameters used to provides
        respectively the http_paths to serve statically, and where to find the
        matching files on the filesystem.
        """
        threading.Thread.__init__(self)
        self.httpd = make_server('', 0, self.pypi_app)
        self.httpd.RequestHandlerClass.log_request = lambda *_: None
        self.address = self.httpd.server_address
        self.request_queue = Queue.Queue()
        self._requests = []
        self.default_response_status = "200 OK"
        self.default_response_headers = [('Content-type', 'text/plain')]
        self.default_response_data = ["hello"]
        self.static_uri_paths = static_uri_paths
        self.static_filesystem_paths = [PYPI_DEFAULT_STATIC_PATH + "/" + path 
            for path in static_filesystem_paths]

    def run(self):
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()
        self.join()

    def pypi_app(self, environ, start_response):
        """Serve the content.

        Also record the requests to be accessed later. If trying to access an
        url matching a static uri, serve static content, otherwise serve 
        what is provided by the `get_next_response` method.
        """
        # record the request. Read the input only on PUT or POST requests
        if environ["REQUEST_METHOD"] in ("PUT", "POST"):
            if environ.get("CONTENT_LENGTH"):
                request_data = environ.pop('wsgi.input').read(
                    int(environ['CONTENT_LENGTH']))
            else:
                request_data = environ.pop('wsgi.input').read()
        elif environ["REQUEST_METHOD"] in ("GET", "DELETE"):
            request_data = ''
            
        self.request_queue.put((environ, request_data))
        
        # serve the content from local disc if we request an URL beginning 
        # by a pattern defined in `static_paths`
        relative_path = environ["PATH_INFO"].replace(self.full_address, '')
        url_parts = relative_path.split("/")
        if len(url_parts) > 1 and url_parts[1] in self.static_uri_paths:
            data = None
            # always take the last first.
            fs_paths = []
            fs_paths.extend(self.static_filesystem_paths)
            fs_paths.reverse()
            for fs_path in fs_paths:
                try:
                    if relative_path.endswith("/"):
                        relative_path += "index.html"
                    print fs_path + relative_path
                    file = open(fs_path + relative_path)
                    data = file.read()
                    start_response("200 OK", [('Content-type', 'text/html')])
                except IOError:
                    pass
            
            if data is None:
                start_response("404 NOT FOUND", [('Content-type', 'text/html')])
                data = "Not Found"
            return data

        # otherwise serve the content from get_next_response
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
