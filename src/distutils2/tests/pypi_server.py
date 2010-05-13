import Queue, threading, time
from wsgiref.simple_server import make_server

class PyPIServer(threading.Thread):
    """Thread that wraps a wsgi app"""
    def __init__(self):
        threading.Thread.__init__(self)
        self.httpd = make_server('', 0, self.pypi_app)
        self.httpd.RequestHandlerClass.log_request = lambda *_: None
        self.address = self.httpd.server_address
        self.request_queue = Queue.Queue()
        self._requests = []

    def run(self):
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()
        self.join()
        time.sleep(0.2)

    def pypi_app(self, environ, start_response):
        status = '200 OK' # HTTP Status
        headers = [('Content-type', 'text/plain')] # HTTP Headers
        start_response(status, headers)
        request_data = environ.pop('wsgi.input').read(int(environ['CONTENT_LENGTH']))
        self.request_queue.put((environ, request_data))
        return ["hello"]

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
