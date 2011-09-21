"""Compatibility helpers.

This module provides individual classes or objects backported from
Python 3.2, for internal use only.  Whole modules are in _backport.
"""

import os
import re
import sys
import codecs
from distutils2 import logger


# XXX Having two classes with the same name is not a good thing.
# XXX 2to3-related code should move from util to this module

try:
    from distutils2.util import Mixin2to3 as _Mixin2to3
    _CONVERT = True
    _KLASS = _Mixin2to3
except ImportError:
    _CONVERT = False
    _KLASS = object

__all__ = ['Mixin2to3']


class Mixin2to3(_KLASS):
    """ The base class which can be used for refactoring. When run under
    Python 3.0, the run_2to3 method provided by Mixin2to3 is overridden.
    When run on Python 2.x, it merely creates a class which overrides run_2to3,
    yet does nothing in particular with it.
    """
    if _CONVERT:

        def _run_2to3(self, files, doctests=[], fixers=[]):
            """ Takes a list of files and doctests, and performs conversion
            on those.
              - First, the files which contain the code(`files`) are converted.
              - Second, the doctests in `files` are converted.
              - Thirdly, the doctests in `doctests` are converted.
            """
            if fixers:
                self.fixer_names = fixers

            logger.info('converting Python code')
            _KLASS.run_2to3(self, files)

            logger.info('converting doctests in Python files')
            _KLASS.run_2to3(self, files, doctests_only=True)

            if doctests != []:
                logger.info('converting doctest in text files')
                _KLASS.run_2to3(self, doctests, doctests_only=True)
    else:
        # If run on Python 2.x, there is nothing to do.

        def _run_2to3(self, files, doctests=[], fixers=[]):
            pass


# The rest of this file does not exist in packaging
# functions are sorted alphabetically and are not included in __all__

try:
    any
except NameError:
    def any(seq):
        for elem in seq:
            if elem:
                return True
        return False


_cookie_re = re.compile("coding[:=]\s*([-\w.]+)")


def _get_normal_name(orig_enc):
    """Imitates get_normal_name in tokenizer.c."""
    # Only care about the first 12 characters.
    enc = orig_enc[:12].lower().replace("_", "-")
    if enc == "utf-8" or enc.startswith("utf-8-"):
        return "utf-8"
    if enc in ("latin-1", "iso-8859-1", "iso-latin-1") or \
       enc.startswith(("latin-1-", "iso-8859-1-", "iso-latin-1-")):
        return "iso-8859-1"
    return orig_enc


def detect_encoding(readline):
    """
    The detect_encoding() function is used to detect the encoding that should
    be used to decode a Python source file.  It requires one argment, readline,
    in the same way as the tokenize() generator.

    It will call readline a maximum of twice, and return the encoding used
    (as a string) and a list of any lines (left as bytes) it has read in.

    It detects the encoding from the presence of a utf-8 bom or an encoding
    cookie as specified in pep-0263.  If both a bom and a cookie are present,
    but disagree, a SyntaxError will be raised.  If the encoding cookie is an
    invalid charset, raise a SyntaxError.  Note that if a utf-8 bom is found,
    'utf-8-sig' is returned.

    If no encoding is specified, then the default of 'utf-8' will be returned.
    """
    bom_found = False
    encoding = None
    default = 'utf-8'

    def read_or_stop():
        try:
            return readline()
        except StopIteration:
            return ''

    def find_cookie(line):
        try:
            line_string = line.decode('ascii')
        except UnicodeDecodeError:
            return None

        matches = _cookie_re.findall(line_string)
        if not matches:
            return None
        encoding = _get_normal_name(matches[0])
        try:
            codec = codecs.lookup(encoding)
        except LookupError:
            # This behaviour mimics the Python interpreter
            raise SyntaxError("unknown encoding: " + encoding)

        if bom_found:
            if codec.name != 'utf-8':
                # This behaviour mimics the Python interpreter
                raise SyntaxError('encoding problem: utf-8')
            encoding += '-sig'
        return encoding

    first = read_or_stop()
    if first.startswith(codecs.BOM_UTF8):
        bom_found = True
        first = first[3:]
        default = 'utf-8-sig'
    if not first:
        return default, []

    encoding = find_cookie(first)
    if encoding:
        return encoding, [first]

    second = read_or_stop()
    if not second:
        return default, [first]

    encoding = find_cookie(second)
    if encoding:
        return encoding, [first, second]

    return default, [first, second]


def fsencode(filename):
    """
    Encode filename to the filesystem encoding with 'surrogateescape' error
    handler, return bytes unchanged. On Windows, use 'strict' error handler if
    the file system encoding is 'mbcs' (which is the default encoding).
    """
    if isinstance(filename, str):
        return filename
    elif isinstance(filename, unicode):
        return filename.encode(sys.getfilesystemencoding())
    else:
        raise TypeError("expect bytes or str, not %s" %
                        type(filename).__name__)


try:
    from functools import wraps
except ImportError:
    def wraps(func=None):
        """No-op replacement for functools.wraps"""
        def wrapped(func):
            return func
        return wrapped

try:
    from platform import python_implementation
except ImportError:
    def python_implementation():
        if 'PyPy' in sys.version:
            return 'PyPy'
        if os.name == 'java':
            return 'Jython'
        if sys.version.startswith('IronPython'):
            return 'IronPython'
        return 'CPython'
