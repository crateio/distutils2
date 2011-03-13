""" distutils2.compat

Used to provide classes, variables and imports which can be used to
support distutils2 across versions(2.x and 3.x)
"""

import logging


# XXX Having two classes with the same name is not a good thing.
# XXX 2to3-related code should move from util to this module

# TODO Move common code here: PY3 (bool indicating if we're on 3.x), any, etc.

try:
    from distutils2.util import Mixin2to3 as _Mixin2to3
    _CONVERT = True
    _KLASS = _Mixin2to3
except ImportError:
    _CONVERT = False
    _KLASS = object

# marking public APIs
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
            # if additional fixers are present, use them
            if fixers:
                self.fixer_names = fixers

            # Convert the ".py" files.
            logging.info("Converting Python code")
            _KLASS.run_2to3(self, files)

            # Convert the doctests in the ".py" files.
            logging.info("Converting doctests with '.py' files")
            _KLASS.run_2to3(self, files, doctests_only=True)

            if doctests != []:
                logging.info("Converting text files which contain doctests")
                _KLASS.run_2to3(self, doctests, doctests_only=True)
    else:
        # If run on Python 2.x, there is nothing to do.
        def _run_2to3(self, files, doctests=[], fixers=[]):
            pass
