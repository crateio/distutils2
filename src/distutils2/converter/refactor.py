"""distutils2.converter.refactor

Provides DistutilsRefactoringTool, a class that register fixers used
to refactor distutils or setuptools packages into distutils2 ones.
"""
from lib2to3.refactor import RefactoringTool

_DISTUTILS_FIXERS = ['distutils2.converter.fixers.fix_imports']

class DistutilsRefactoringTool(RefactoringTool):

    def __init__(self, fixer_names=_DISTUTILS_FIXERS, options=None,
                 explicit=None):

        super(DistutilsRefactoringTool, self).__init__(fixer_names, options,
                                                       explicit)

