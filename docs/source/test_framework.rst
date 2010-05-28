==============
Test Framework
==============

When you are testing code that works with distutils, you might find these tools
useful.


``PyPIServer``
==============

PyPIServer is a class that implements an HTTP server running in a separate
thread. All it does is record the requests for further inspection. The recorded
data is available under ``requests`` attribute. The default
HTTP response can be overriden with the ``default_response_status``,
``default_response_headers`` and ``default_response_data`` attributes.


``PyPIServerTestCase``
======================

``PyPIServerTestCase`` is a test case class with setUp and tearDown methods that
take care of a single PyPIServer instance attached as a ``pypi`` attribute on
the test class. Use it as one of the base classes in you test case::

  class UploadTestCase(PyPIServerTestCase):
      def test_something(self):
          cmd = self.prepare_command()
          cmd.ensure_finalized()
          cmd.repository = self.pypi.full_address
          cmd.run()

          environ, request_data = self.pypi.requests[-1]
          self.assertEqual(request_data, EXPECTED_REQUEST_DATA)
