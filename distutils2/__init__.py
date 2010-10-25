"""distutils

Third-party tools can use parts of Distutils2 as building blocks
without causing the other modules to be imported:

    import distutils2.version
    import distutils2.pypi.simple
    import distutils2.tests.pypi_server
"""
from logging import getLogger

__all__ = ['__version__', 'logger']

__version__ = "1.0a3"
logger = getLogger('distutils2')


# when set to True, converts doctests by default too
run_2to3_on_doctests = True
# Standard package names for fixer packages
lib2to3_fixer_packages = ['lib2to3.fixes']
