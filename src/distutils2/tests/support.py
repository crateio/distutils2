"""Support code for distutils2 test cases.

Always import unittest from this module, it will be the right version
(standard library unittest for 2.7 and higher, third-party unittest2
release for older versions).
"""

import os
import sys
import shutil
import tempfile
from copy import deepcopy
import warnings

from distutils2 import log
from distutils2.log import DEBUG, INFO, WARN, ERROR, FATAL

if sys.version_info >= (2, 7):
    # improved unittest package from 2.7's standard library
    import unittest
else:
    # external release of same package for older versions
    import unittest2 as unittest

class LoggingSilencer(object):

    def setUp(self):
        super(LoggingSilencer, self).setUp()
        self.threshold = log.set_threshold(log.FATAL)
        # catching warnings
        # when log will be replaced by logging
        # we won't need such monkey-patch anymore
        self._old_log = log.Log._log
        log.Log._log = self._log
        self.logs = []

    def tearDown(self):
        log.set_threshold(self.threshold)
        log.Log._log = self._old_log
        super(LoggingSilencer, self).tearDown()

    def _log(self, level, msg, args):
        if level not in (DEBUG, INFO, WARN, ERROR, FATAL):
            raise ValueError('%s wrong log level' % level)
        self.logs.append((level, msg, args))

    def get_logs(self, *levels):
        def _format(msg, args):
            if len(args) == 0:
                return msg
            return msg % args
        return [_format(msg, args) for level, msg, args
                in self.logs if level in levels]

    def clear_logs(self):
        self.logs = []

class TempdirManager(object):
    """Mix-in class that handles temporary directories for test cases.

    This is intended to be used with unittest.TestCase.
    """

    def setUp(self):
        super(TempdirManager, self).setUp()
        self.tempdirs = []
        self.tempfiles = []

    def tearDown(self):
        super(TempdirManager, self).tearDown()
        while self.tempdirs:
            d = self.tempdirs.pop()
            shutil.rmtree(d, os.name in ('nt', 'cygwin'))
        for file_ in self.tempfiles:
            if os.path.exists(file_):
                os.remove(file_)

    def mktempfile(self, *args, **kwargs):
        """Create a temporary file that will be cleaned up."""
        tempfile_ = tempfile.NamedTemporaryFile(*args, **kwargs)
        self.tempfiles.append(tempfile_.name)
        return tempfile_

    def mkdtemp(self):
        """Create a temporary directory that will be cleaned up.

        Returns the path of the directory.
        """
        d = tempfile.mkdtemp()
        self.tempdirs.append(d)
        return d

    def write_file(self, path, content='xxx'):
        """Writes a file in the given path.


        path can be a string or a sequence.
        """
        if isinstance(path, (list, tuple)):
            path = os.path.join(*path)
        f = open(path, 'w')
        try:
            f.write(content)
        finally:
            f.close()

    def create_dist(self, pkg_name='foo', **kw):
        """Will generate a test environment.

        This function creates:
         - a Distribution instance using keywords
         - a temporary directory with a package structure

        It returns the package directory and the distribution
        instance.
        """
        from distutils2.dist import Distribution
        tmp_dir = self.mkdtemp()
        pkg_dir = os.path.join(tmp_dir, pkg_name)
        os.mkdir(pkg_dir)
        dist = Distribution(attrs=kw)

        return pkg_dir, dist

class DummyCommand:
    """Class to store options for retrieval via set_undefined_options()."""

    def __init__(self, **kwargs):
        for kw, val in kwargs.items():
            setattr(self, kw, val)

    def ensure_finalized(self):
        pass

class EnvironGuard(object):

    def setUp(self):
        super(EnvironGuard, self).setUp()
        self.old_environ = deepcopy(os.environ)

    def tearDown(self):
        for key, value in self.old_environ.items():
            if os.environ.get(key) != value:
                os.environ[key] = value

        for key in os.environ.keys():
            if key not in self.old_environ:
                del os.environ[key]

        super(EnvironGuard, self).tearDown()
