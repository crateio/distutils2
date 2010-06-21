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


class DownloadError(PyPIError):
    """An error has occurs while downloading"""


class MD5HashDoesNotMatch(DownloadError):
    """Compared MD5 hashes does not match"""
