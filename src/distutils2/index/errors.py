"""distutils2.pypi.errors

All errors and exceptions raised by PyPiIndex classes.
"""
from distutils2.errors import DistutilsError


class IndexError(DistutilsError):
    """The base class for errors of the index python package."""


class ProjectNotFound(IndexError):
    """Project has not been found"""


class DistributionNotFound(IndexError):
    """No distribution match the given requirements."""


class CantParseArchiveName(IndexError):
    """An archive name can't be parsed to find distribution name and version"""


class DownloadError(IndexError):
    """An error has occurs while downloading"""


class HashDoesNotMatch(DownloadError):
    """Compared hashes does not match"""


class UnsupportedHashName(IndexError):
    """A unsupported hashname has been used"""


class UnableToDownload(IndexError):
    """All mirrors have been tried, without success"""


class InvalidSearchField(IndexError):
    """An invalid search field has been used"""
