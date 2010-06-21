"""distutils2.pypi.errors

All errors and exceptions raised by PyPiIndex classes.
"""
from distutils2.errors import DistutilsError


class PyPIError(DistutilsError):
    """The base class for errors of the pypi python package."""

class DistributionNotFound(PyPIError):
    """No distribution match the given requirements."""

class CantParseArchiveName(PyPIError):
    """An archive name can't be parsed to find distribution name and version"""
