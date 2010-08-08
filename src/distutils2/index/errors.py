"""distutils2.pypi.errors

All errors and exceptions raised by PyPiIndex classes.
"""
from distutils2.errors import DistutilsError


class IndexesError(DistutilsError):
    """The base class for errors of the index python package."""


class ProjectNotFound(IndexesError):
    """Project has not been found"""


class DistributionNotFound(IndexesError):
    """The release has not been found"""


class ReleaseNotFound(IndexesError):
    """The release has not been found"""


class CantParseArchiveName(IndexesError):
    """An archive name can't be parsed to find distribution name and version"""


class DownloadError(IndexesError):
    """An error has occurs while downloading"""


class HashDoesNotMatch(DownloadError):
    """Compared hashes does not match"""


class UnsupportedHashName(IndexesError):
    """A unsupported hashname has been used"""


class UnableToDownload(IndexesError):
    """All mirrors have been tried, without success"""


class InvalidSearchField(IndexesError):
    """An invalid search field has been used"""
