========
Commands
========

Distutils2 provides a set of commands that are not present in distutils itself.
You might recognize some of them from other projects, like Distribute or
Setuptools.


``test`` - Build package and run a unittest suite
=================================================

When doing test-driven development, or running automated builds that need
testing before they are deployed for downloading or use, it's often useful
to be able to run a project's unit tests without actually deploying the project
anywhere, even using the ``develop`` command.  The ``test`` command runs a
project's unit tests without actually deploying it, by temporarily putting the
project's source on ``sys.path``, after first running ``build_ext -i`` and
``egg_info`` to ensure that any C extensions and project metadata are
up-to-date.

To use this command, your project's tests must be wrapped in a ``unittest``
test suite by either a function, a ``TestCase`` class or method, or a module
or package containing ``TestCase`` classes.  If the named suite is a module,
and the module has an ``additional_tests()`` function, it is called and the
result (which must be a ``unittest.TestSuite``) is added to the tests to be
run.  If the named suite is a package, any submodules and subpackages are
recursively added to the overall test suite.  (Note: if your project specifies
a ``test_loader``, the rules for processing the chosen ``test_suite`` may
differ; see the `test_loader`_ documentation for more details.)

Note that many test systems including ``doctest`` support wrapping their
non-``unittest`` tests in ``TestSuite`` objects.  So, if you are using a test
package that does not support this, we suggest you encourage its developers to
implement test suite support, as this is a convenient and standard way to
aggregate a collection of tests to be run under a common test harness.

By default, tests will be run in the "verbose" mode of the ``unittest``
package's text test runner, but you can get the "quiet" mode (just dots) if
you supply the ``-q`` or ``--quiet`` option, either as a global option to
the setup script (e.g. ``setup.py -q test``) or as an option for the ``test``
command itself (e.g. ``setup.py test -q``).  There is one other option
available:

``--test-suite=NAME, -s NAME``
    Specify the test suite (or module, class, or method) to be run
    (e.g. ``some_module.test_suite``).  The default for this option can be
    set by giving a ``test_suite`` argument to the ``setup()`` function, e.g.::

        setup(
            # ...
            test_suite = "my_package.tests.test_all"
        )

    If you did not set a ``test_suite`` in your ``setup()`` call, and do not
    provide a ``--test-suite`` option, an error will occur.


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
    The directory to be uploaded to the repository. The default value is
    ``docs`` in project root.

``--show-response``
    Display the full response text from server; this is useful for debugging
    PyPI problems.

``--repository=URL, -r URL``
    The URL of the repository to upload to.  Defaults to
    http://pypi.python.org/pypi (i.e., the main PyPI installation).


