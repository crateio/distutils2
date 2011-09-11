"""Support code for distutils2 test cases.

A few helper classes are provided: LoggingCatcher, TempdirManager and
EnvironRestorer. They are written to be used as mixins::

    from distutils2.tests import unittest
    from distutils2.tests.support import LoggingCatcher

    class SomeTestCase(LoggingCatcher, unittest.TestCase):

If you need to define a setUp method on your test class, you have to
call the mixin class' setUp method or it won't work (same thing for
tearDown):

        def setUp(self):
            super(SomeTestCase, self).setUp()
            ... # other setup code

Also provided is a DummyCommand class, useful to mock commands in the
tests of another command that needs them, a create_distribution function
and a skip_unless_symlink decorator.

Also provided is a DummyCommand class, useful to mock commands in the
tests of another command that needs them, a create_distribution function
and a skip_unless_symlink decorator.

Each class or function has a docstring to explain its purpose and usage.
"""

import codecs
import os
import shutil
import logging
import logging.handlers
import subprocess
import sys
import weakref
import tempfile
try:
    import _thread, threading
except ImportError:
    _thread = None
    threading = None
try:
    import zlib
except ImportError:
    zlib = None

from distutils2.dist import Distribution
from distutils2.tests import unittest

__all__ = ['LoggingCatcher', 'TempdirManager', 'EnvironRestorer',
           'DummyCommand', 'unittest', 'create_distribution',
           'skip_unless_symlink', 'requires_zlib']


logger = logging.getLogger('distutils2')
logger2to3 = logging.getLogger('RefactoringTool')


class _TestHandler(logging.handlers.BufferingHandler):
    # stolen and adapted from test.support

    def __init__(self):
        logging.handlers.BufferingHandler.__init__(self, 0)
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
    them.  get_logs automatically flushes the logs; if you test code that
    generates logging messages but don't use get_logs, you have to flush
    manually before doing other checks on logging message, otherwise you
    will get irrelevant results.  See example in test_command_check.
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

    def get_logs(self, *levels):
        """Return all log messages with level in *levels*.

        Without explicit levels given, returns all messages.  *levels* defaults
        to all levels.  For log calls with arguments (i.e.
        logger.info('bla bla %r', arg)), the messages will be formatted before
        being returned (e.g. "bla bla 'thing'").

        Returns a list.  Automatically flushes the loghandler after being
        called.

        Example: self.get_logs(logging.WARN, logging.DEBUG).
        """
        if not levels:
            messages = [log.getMessage() for log in self.loghandler.buffer]
        else:
            messages = [log.getMessage() for log in self.loghandler.buffer
                        if log.levelno in levels]
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
        f.write(content)
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


def create_distribution(configfiles=()):
    """Prepares a distribution with given config files parsed."""
    d = TestDistribution()
    d.config.find_config_files = d.find_config_files
    d._config_files = configfiles
    d.parse_config_files()
    d.parse_command_line()
    return d


def fake_dec(*args, **kw):
    """Fake decorator"""
    def _wrap(func):
        def __wrap(*args, **kw):
            return func(*args, **kw)
        return __wrap
    return _wrap


#try:
#    from test.support import skip_unless_symlink
#except ImportError:
#    skip_unless_symlink = unittest.skip(
#        'requires test.support.skip_unless_symlink')

if os.name == 'java':
    # Jython disallows @ in module names
    TESTFN = '$test'
else:
    TESTFN = '@test'

# Disambiguate TESTFN for parallel testing, while letting it remain a valid
# module name.
TESTFN = "%s_%s_tmp" % (TESTFN, os.getpid())


# TESTFN_UNICODE is a non-ascii filename
TESTFN_UNICODE = TESTFN + "-\xe0\xf2\u0258\u0141\u011f"
if sys.platform == 'darwin':
    # In Mac OS X's VFS API file names are, by definition, canonically
    # decomposed Unicode, encoded using UTF-8. See QA1173:
    # http://developer.apple.com/mac/library/qa/qa2001/qa1173.html
    import unicodedata
    TESTFN_UNICODE = unicodedata.normalize('NFD', TESTFN_UNICODE)
TESTFN_ENCODING = sys.getfilesystemencoding()

# TESTFN_UNENCODABLE is a filename (str type) that should *not* be able to be
# encoded by the filesystem encoding (in strict mode). It can be None if we
# cannot generate such filename.
TESTFN_UNENCODABLE = None
if os.name in ('nt', 'ce'):
    # skip win32s (0) or Windows 9x/ME (1)
    if sys.getwindowsversion().platform >= 2:
        # Different kinds of characters from various languages to minimize the
        # probability that the whole name is encodable to MBCS (issue #9819)
        TESTFN_UNENCODABLE = TESTFN + "-\u5171\u0141\u2661\u0363\uDC80"
        try:
            TESTFN_UNENCODABLE.encode(TESTFN_ENCODING)
        except UnicodeEncodeError:
            pass
        else:
            print ('WARNING: The filename %r CAN be encoded by the filesystem encoding (%s). '
                   'Unicode filename tests may not be effective'
                   % (TESTFN_UNENCODABLE, TESTFN_ENCODING))
            TESTFN_UNENCODABLE = None
# Mac OS X denies unencodable filenames (invalid utf-8)
elif sys.platform != 'darwin':
    try:
        # ascii and utf-8 cannot encode the byte 0xff
        '\xff'.decode(TESTFN_ENCODING)
    except UnicodeDecodeError:
        # 0xff will be encoded using the surrogate character u+DCFF
        try:
            TESTFN_UNENCODABLE = TESTFN \
                + '-\xff'.decode(TESTFN_ENCODING, 'surrogateescape')
        except LookupError:
            pass
    else:
        # File system encoding (eg. ISO-8859-* encodings) can encode
        # the byte 0xff. Skip some unicode filename tests.
        pass

def unlink(filename):
    try:
        os.unlink(filename)
    except OSError:
        error = sys.exc_info()[1]
        # The filename need not exist.
        if error.errno not in (errno.ENOENT, errno.ENOTDIR):
            raise

def _filter_suite(suite, pred):
    """Recursively filter test cases in a suite based on a predicate."""
    newtests = []
    for test in suite._tests:
        if isinstance(test, unittest.TestSuite):
            _filter_suite(test, pred)
            newtests.append(test)
        else:
            if pred(test):
                newtests.append(test)
    suite._tests = newtests

class Error(Exception):
    """Base class for regression test exceptions."""

class TestFailed(Error):
    """Test failed."""


verbose = True
failfast = False

def _run_suite(suite):
    """Run tests from a unittest.TestSuite-derived class."""
    if verbose:
        runner = unittest.TextTestRunner(sys.stdout, verbosity=2,
                                         failfast=failfast)
    else:
        runner = BasicTestRunner()

    result = runner.run(suite)
    if not result.wasSuccessful():
        if len(result.errors) == 1 and not result.failures:
            err = result.errors[0][1]
        elif len(result.failures) == 1 and not result.errors:
            err = result.failures[0][1]
        else:
            err = "multiple errors occurred"
            if not verbose: err += "; run in verbose mode for details"
        raise TestFailed(err)

match_tests = None

def run_unittest(*classes):
    """Run tests from unittest.TestCase-derived classes."""
    valid_types = (unittest.TestSuite, unittest.TestCase)
    suite = unittest.TestSuite()
    for cls in classes:
        if isinstance(cls, basestring):
            if cls in sys.modules:
                suite.addTest(unittest.findTestCases(sys.modules[cls]))
            else:
                raise ValueError("str arguments must be keys in sys.modules")
        elif isinstance(cls, valid_types):
            suite.addTest(cls)
        else:
            suite.addTest(unittest.makeSuite(cls))
    def case_pred(test):
        if match_tests is None:
            return True
        for name in test.id().split("."):
            if fnmatch.fnmatchcase(name, match_tests):
                return True
        return False
    _filter_suite(suite, case_pred)
    _run_suite(suite)


def reap_threads(func):
    """Use this function when threads are being used.  This will
    ensure that the threads are cleaned up even when the test fails.
    If threading is unavailable this function does nothing.
    """
    if not _thread:
        return func

    @functools.wraps(func)
    def decorator(*args):
        key = threading_setup()
        try:
            return func(*args)
        finally:
            threading_cleanup(*key)
    return decorator

def reap_children():
    """Use this function at the end of test_main() whenever sub-processes
    are started.  This will help ensure that no extra children (zombies)
    stick around to hog resources and create problems when looking
    for refleaks.
    """

    # Reap all our dead child processes so we don't leave zombies around.
    # These hog resources and might be causing some of the buildbots to die.
    if hasattr(os, 'waitpid'):
        any_process = -1
        while True:
            try:
                # This will raise an exception on Windows.  That's ok.
                pid, status = os.waitpid(any_process, os.WNOHANG)
                if pid == 0:
                    break
            except:
                break

requires_zlib = unittest.skipUnless(zlib, 'requires zlib')

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
    err =  strip_python_stderr(err)
    if (rc and expected_success) or (not rc and not expected_success):
        raise AssertionError(
            "Process return code is %d, "
            "stderr follows:\n%s" % (rc, err.decode('ascii', 'ignore')))
    return rc, out, err

def assert_python_ok(*args, **env_vars):
    """
    Assert that running the interpreter with `args` and optional environment
    variables `env_vars` is ok and return a (return code, stdout, stderr) tuple.
    """
    return _assert_python(True, *args, **env_vars)

def unload(name):
    try:
        del sys.modules[name]
    except KeyError:
        pass

