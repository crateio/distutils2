"""Support code for distutils2 test cases.

*This module should not be considered public: its content and API may
change in incompatible ways.*

A few helper classes are provided: LoggingCatcher, TempdirManager and
EnvironRestorer. They are written to be used as mixins::

    from distutils2.tests import unittest
    from distutils2.tests.support import LoggingCatcher

    class SomeTestCase(LoggingCatcher, unittest.TestCase):
        ...

If you need to define a setUp method on your test class, you have to
call the mixin class' setUp method or it won't work (same thing for
tearDown):

        def setUp(self):
            super(SomeTestCase, self).setUp()
            ...  # other setup code

Also provided is a DummyCommand class, useful to mock commands in the
tests of another command that needs them, for example to fake
compilation in build_ext (this requires that the mock build_ext command
be injected into the distribution object's command_obj dictionary).

For tests that need to compile an extension module, use the
copy_xxmodule_c and fixup_build_ext functions.

Each class or function has a docstring to explain its purpose and usage.
Existing tests should also be used as examples.
"""

import os
import re
import sys
import errno
import codecs
import logging
import logging.handlers
import subprocess
import weakref
import tempfile
try:
    import zlib
except ImportError:
    zlib = None
try:
    import docutils
except ImportError:
    docutils = None

from distutils2.dist import Distribution
from distutils2.util import resolve_name
from distutils2.command import set_command, _COMMANDS

from distutils2.tests import unittest
from distutils2._backport import shutil, sysconfig

# define __all__ to make pydoc more useful
__all__ = [
    # TestCase mixins
    'LoggingCatcher', 'TempdirManager', 'EnvironRestorer',
    # mocks
    'DummyCommand', 'TestDistribution', 'Inputs',
    # misc. functions and decorators
    'fake_dec', 'create_distribution', 'use_command',
    'copy_xxmodule_c', 'fixup_build_ext',
    'requires_py26_min', 'skip_2to3_optimize', 'requires_docutils',
    # imported from this module for backport purposes
    'unittest', 'requires_zlib', 'skip_unless_symlink',
]


logger = logging.getLogger('distutils2')
logger2to3 = logging.getLogger('RefactoringTool')


class _TestHandler(logging.handlers.BufferingHandler, object):
    # stolen and adapted from test.support

    def __init__(self):
        super(_TestHandler, self).__init__(0)
        self.setLevel(logging.DEBUG)

    def shouldFlush(self):
        return False

    def emit(self, record):
        self.buffer.append(record)


class LoggingCatcher(object):
    """TestCase-compatible mixin to receive logging calls.

    Upon setUp, instances of this classes get a BufferingHandler that's
    configured to record all messages logged to the 'distutils2' logger.

    Use get_logs to retrieve messages and self.loghandler.flush to discard
    them.  get_logs automatically flushes the logs, unless you pass
    *flush=False*, for example to make multiple calls to the method with
    different level arguments.  If your test calls some code that generates
    logging message and then you don't call get_logs, you will need to flush
    manually before testing other code in the same test_* method, otherwise
    get_logs in the next lines will see messages from the previous lines.
    See example in test_command_check.
    """

    def setUp(self):
        super(LoggingCatcher, self).setUp()
        self.loghandler = handler = _TestHandler()
        self._old_levels = logger.level, logger2to3.level
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)  # we want all messages
        logger2to3.setLevel(logging.CRITICAL)  # we don't want 2to3 messages

    def tearDown(self):
        handler = self.loghandler
        # All this is necessary to properly shut down the logging system and
        # avoid a regrtest complaint.  Thanks to Vinay Sajip for the help.
        handler.close()
        logger.removeHandler(handler)
        for ref in weakref.getweakrefs(handler):
            logging._removeHandlerRef(ref)
        del self.loghandler
        logger.setLevel(self._old_levels[0])
        logger2to3.setLevel(self._old_levels[1])
        super(LoggingCatcher, self).tearDown()

    def get_logs(self, level=logging.WARNING, flush=True):
        """Return all log messages with given level.

        *level* defaults to logging.WARNING.

        For log calls with arguments (i.e.  logger.info('bla bla %r', arg)),
        the messages will be formatted before being returned (e.g. "bla bla
        'thing'").

        Returns a list.  Automatically flushes the loghandler after being
        called, unless *flush* is False (this is useful to get e.g. all
        warnings then all info messages).
        """
        messages = [log.getMessage() for log in self.loghandler.buffer
                    if log.levelno == level]
        if flush:
            self.loghandler.flush()
        return messages


class TempdirManager(object):
    """TestCase-compatible mixin to create temporary directories and files.

    Directories and files created in a test_* method will be removed after it
    has run.
    """

    def setUp(self):
        super(TempdirManager, self).setUp()
        self._olddir = os.getcwd()
        self._basetempdir = tempfile.mkdtemp()
        self._files = []

    def tearDown(self):
        for handle, name in self._files:
            handle.close()
            unlink(name)

        os.chdir(self._olddir)
        shutil.rmtree(self._basetempdir)
        super(TempdirManager, self).tearDown()

    def mktempfile(self):
        """Create a read-write temporary file and return it."""
        fd, fn = tempfile.mkstemp(dir=self._basetempdir)
        os.close(fd)
        fp = open(fn, 'w+')
        self._files.append((fp, fn))
        return fp

    def mkdtemp(self):
        """Create a temporary directory and return its path."""
        d = tempfile.mkdtemp(dir=self._basetempdir)
        return d

    def write_file(self, path, content='xxx', encoding=None):
        """Write a file at the given path.

        path can be a string, a tuple or a list; if it's a tuple or list,
        os.path.join will be used to produce a path.
        """
        if isinstance(path, (list, tuple)):
            path = os.path.join(*path)
        f = codecs.open(path, 'w', encoding=encoding)
        try:
            f.write(content)
        finally:
            f.close()

    def create_dist(self, **kw):
        """Create a stub distribution object and files.

        This function creates a Distribution instance (use keyword arguments
        to customize it) and a temporary directory with a project structure
        (currently an empty directory).

        It returns the path to the directory and the Distribution instance.
        You can use self.write_file to write any file in that
        directory, e.g. setup scripts or Python modules.
        """
        if 'name' not in kw:
            kw['name'] = 'foo'
        tmp_dir = self.mkdtemp()
        project_dir = os.path.join(tmp_dir, kw['name'])
        os.mkdir(project_dir)
        dist = Distribution(attrs=kw)
        return project_dir, dist

    def assertIsFile(self, *args):
        path = os.path.join(*args)
        dirname = os.path.dirname(path)
        file = os.path.basename(path)
        if os.path.isdir(dirname):
            files = os.listdir(dirname)
            msg = "%s not found in %s: %s" % (file, dirname, files)
            assert os.path.isfile(path), msg
        else:
            raise AssertionError(
                    '%s not found. %s does not exist' % (file, dirname))

    def assertIsNotFile(self, *args):
        path = os.path.join(*args)
        self.assertFalse(os.path.isfile(path), "%r exists" % path)


class EnvironRestorer(object):
    """TestCase-compatible mixin to restore or delete environment variables.

    The variables to restore (or delete if they were not originally present)
    must be explicitly listed in self.restore_environ.  It's better to be
    aware of what we're modifying instead of saving and restoring the whole
    environment.
    """

    def setUp(self):
        super(EnvironRestorer, self).setUp()
        self._saved = []
        self._added = []
        for key in self.restore_environ:
            if key in os.environ:
                self._saved.append((key, os.environ[key]))
            else:
                self._added.append(key)

    def tearDown(self):
        for key, value in self._saved:
            os.environ[key] = value
        for key in self._added:
            os.environ.pop(key, None)
        super(EnvironRestorer, self).tearDown()


class DummyCommand(object):
    """Class to store options for retrieval via set_undefined_options().

    Useful for mocking one dependency command in the tests for another
    command, see e.g. the dummy build command in test_build_scripts.
    """
    # XXX does not work with dist.reinitialize_command, which typechecks
    # and wants a finalized attribute

    def __init__(self, **kwargs):
        for kw, val in kwargs.items():
            setattr(self, kw, val)

    def ensure_finalized(self):
        pass


class TestDistribution(Distribution):
    """Distribution subclasses that avoids the default search for
    configuration files.

    The ._config_files attribute must be set before
    .parse_config_files() is called.
    """

    def find_config_files(self):
        return self._config_files


class Inputs(object):
    """Fakes user inputs."""
    # TODO document usage
    # TODO use context manager or something for auto cleanup

    def __init__(self, *answers):
        self.answers = answers
        self.index = 0

    def __call__(self, prompt=''):
        try:
            return self.answers[self.index]
        finally:
            self.index += 1


def create_distribution(configfiles=()):
    """Prepares a distribution with given config files parsed."""
    d = TestDistribution()
    d.config.find_config_files = d.find_config_files
    d._config_files = configfiles
    d.parse_config_files()
    d.parse_command_line()
    return d


def use_command(testcase, fullname):
    """Register command at *fullname* for the duration of a test."""
    set_command(fullname)
    # XXX maybe set_command should return the class object
    name = resolve_name(fullname).get_command_name()
    # XXX maybe we need a public API to remove commands
    testcase.addCleanup(_COMMANDS.__delitem__, name)


def fake_dec(*args, **kw):
    """Fake decorator"""
    def _wrap(func):
        def __wrap(*args, **kw):
            return func(*args, **kw)
        return __wrap
    return _wrap


def copy_xxmodule_c(directory):
    """Helper for tests that need the xxmodule.c source file.

    Example use:

        def test_compile(self):
            copy_xxmodule_c(self.tmpdir)
            self.assertIn('xxmodule.c', os.listdir(self.tmpdir))

    If the source file can be found, it will be copied to *directory*.  If not,
    the test will be skipped.  Errors during copy are not caught.
    """
    filename = _get_xxmodule_path()
    if filename is None:
        raise unittest.SkipTest('cannot find xxmodule.c')
    shutil.copy(filename, directory)


def _get_xxmodule_path():
    path = os.path.join(os.path.dirname(__file__), 'xxmodule.c')
    if os.path.exists(path):
        return path


def fixup_build_ext(cmd):
    """Function needed to make build_ext tests pass.

    When Python was built with --enable-shared on Unix, -L. is not enough to
    find libpython<blah>.so, because regrtest runs in a tempdir, not in the
    source directory where the .so lives.  (Mac OS X embeds absolute paths
    to shared libraries into executables, so the fixup is a no-op on that
    platform.)

    When Python was built with in debug mode on Windows, build_ext commands
    need their debug attribute set, and it is not done automatically for
    some reason.

    This function handles both of these things, and also fixes
    cmd.distribution.include_dirs if the running Python is an uninstalled
    build.  Example use:

        cmd = build_ext(dist)
        support.fixup_build_ext(cmd)
        cmd.ensure_finalized()
    """
    if os.name == 'nt':
        cmd.debug = sys.executable.endswith('_d.exe')
    elif sysconfig.get_config_var('Py_ENABLE_SHARED'):
        # To further add to the shared builds fun on Unix, we can't just add
        # library_dirs to the Extension() instance because that doesn't get
        # plumbed through to the final compiler command.
        runshared = sysconfig.get_config_var('RUNSHARED')
        if runshared is None:
            cmd.library_dirs = ['.']
        else:
            if sys.platform == 'darwin':
                cmd.library_dirs = []
            else:
                # FIXME no partition in 2.4
                name, equals, value = runshared.partition('=')
                cmd.library_dirs = value.split(os.pathsep)

    # Allow tests to run with an uninstalled Python
    if sysconfig.is_python_build():
        pysrcdir = sysconfig.get_config_var('projectbase')
        cmd.distribution.include_dirs.append(os.path.join(pysrcdir, 'Include'))


try:
    from test.test_support import skip_unless_symlink
except ImportError:
    skip_unless_symlink = unittest.skip(
        'requires test.test_support.skip_unless_symlink')

skip_2to3_optimize = unittest.skipUnless(__debug__,
                                         "2to3 doesn't work under -O")

requires_py26_min = unittest.skipIf(sys.version_info[:2] < (2, 6),
                                    'requires Python 2.6 or higher')

requires_zlib = unittest.skipUnless(zlib, 'requires zlib')

requires_docutils = unittest.skipUnless(docutils, 'requires docutils')


def unlink(filename):
    try:
        os.unlink(filename)
    except OSError, error:
        # The filename need not exist.
        if error.errno not in (errno.ENOENT, errno.ENOTDIR):
            raise


def strip_python_stderr(stderr):
    """Strip the stderr of a Python process from potential debug output
    emitted by the interpreter.

    This will typically be run on the result of the communicate() method
    of a subprocess.Popen object.
    """
    stderr = re.sub(r"\[\d+ refs\]\r?\n?$", "", stderr).strip()
    return stderr


# Executing the interpreter in a subprocess
def _assert_python(expected_success, *args, **env_vars):
    cmd_line = [sys.executable]
    if not env_vars:
        cmd_line.append('-E')
    cmd_line.extend(args)
    # Need to preserve the original environment, for in-place testing of
    # shared library builds.
    env = os.environ.copy()
    env.update(env_vars)
    p = subprocess.Popen(cmd_line, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         env=env)
    try:
        out, err = p.communicate()
    finally:
        subprocess._cleanup()
        p.stdout.close()
        p.stderr.close()
    rc = p.returncode
    err = strip_python_stderr(err)
    if (rc and expected_success) or (not rc and not expected_success):
        raise AssertionError(
            "Process return code is %d, "
            "stderr follows:\n%s" % (rc, err.decode('ascii', 'ignore')))
    return rc, out, err


def assert_python_ok(*args, **env_vars):
    """
    Assert that running the interpreter with `args` and optional environment
    variables `env_vars` is ok and return a (return code, stdout, stderr)
    tuple.
    """
    return _assert_python(True, *args, **env_vars)


def assert_python_failure(*args, **env_vars):
    """
    Assert that running the interpreter with `args` and optional environment
    variables `env_vars` fails and return a (return code, stdout, stderr)
    tuple.
    """
    return _assert_python(False, *args, **env_vars)


def unload(name):
    try:
        del sys.modules[name]
    except KeyError:
        pass
