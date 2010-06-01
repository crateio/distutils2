"""distutils2.converter.refactor

Provides DistutilsRefactoringTool, a class that register fixers used
to refactor distutils or setuptools packages into distutils2 ones.
"""
try:
    from lib2to3.refactor import RefactoringTool
    _LIB2TO3 = True
except ImportError:
    # we need 2.6 at least to run this
    _LIB2TO3 = False

_DISTUTILS_FIXERS = ['distutils2.converter.fixers.fix_imports',
                     'distutils2.converter.fixers.fix_setup_options']

if _LIB2TO3:
    class DistutilsRefactoringTool(RefactoringTool):

        def __init__(self, fixer_names=_DISTUTILS_FIXERS, options=None,
                    explicit=None):

            super(DistutilsRefactoringTool, self).__init__(fixer_names, options,
                                                            explicit)
else:
    class DistutilsRefactoringTool(object):
        def __init__(self, *args, **kw):
            raise NotImplementedError('Not available if run from Python < 2.6')

