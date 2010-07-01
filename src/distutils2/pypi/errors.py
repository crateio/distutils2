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


class HashDoesNotMatch(DownloadError):
    """Compared hashes does not match"""


class UnsupportedHashName(PyPIError):
    """A unsupported hashname has been used"""


class UnableToDownload(PyPIError):
    """All mirrors have been tried, without success"""
