========
Commands
========

Distutils2 provides a set of commands that are not present in distutils itself.
You might recognize some of them from other projects, like Distribute or
Setuptools.

``upload_docs`` - Upload package documentation to PyPI
======================================================

PyPI now supports uploading project documentation to the dedicated URL
http://packages.python.org/<project>/.

The ``upload_docs`` command will create the necessary zip file out of a
documentation directory and will post to the repository.

Note that to upload the documentation of a project, the corresponding version
must already be registered with PyPI, using the distutils ``register``
command -- just like the ``upload`` command.

Assuming there is an ``Example`` project with documentation in the
subdirectory ``docs``, e.g.::

  Example/
  |-- example.py
  |-- setup.cfg
  |-- setup.py
  |-- docs
  |   |-- build
  |   |   `-- html
  |   |   |   |-- index.html
  |   |   |   `-- tips_tricks.html
  |   |-- conf.py
  |   |-- index.txt
  |   `-- tips_tricks.txt

You can simply pass the documentation directory path to the ``upload_docs``
command::

    python setup.py upload_docs --upload-dir=docs/build/html

As with any other ``setuptools`` based command, you can define useful
defaults in the ``setup.cfg`` of your Python project, e.g.:

.. code-block:: ini

    [upload_docs]
    upload-dir = docs/build/html

The ``upload_docs`` command has the following options:

``--upload-dir``
    The directory to be uploaded to the repository.

``--show-response``
    Display the full response text from server; this is useful for debugging
    PyPI problems.

``--repository=URL, -r URL``
    The URL of the repository to upload to.  Defaults to
    http://pypi.python.org/pypi (i.e., the main PyPI installation).


