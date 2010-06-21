"""distutils2.pypi.dist

Provides the PyPIDistribution class thats represents a distribution retreived 
on PyPI.
"""
import re
import urlparse
import urllib
import tempfile
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

from distutils2.version import suggest_normalized_version 
from distutils2.pypi.errors import MD5HashDoesNotMatch

EXTENSIONS = ".tar.gz .tar.bz2 .tar .zip .tgz .egg".split()
MD5_HASH = re.compile(r'^.*#md5=([a-f0-9]+)$')

class PyPIDistribution(object):
    """Represents a distribution retreived from PyPI.

    This is a simple container for various attributes as name, version, 
    location, url etc.

    The PyPIDistribution class is used by the pypi.*Index class to return
    information about distributions. 
    """

    @classmethod
    def from_url(cls, url, probable_dist_name=None):
        """Build a Distribution from a url archive (egg or zip or tgz).

        :param url: complete url of the distribution
        :param probable_dist_name: the probable name of the distribution. This 
        could be useful when multiple name can be assumed from the archive 
        name.
        """
        # if the url contains a md5 hash, get it.
        md5_hash = None
        match = MD5_HASH.match(url)
        if match is not None:
            md5_hash = match.group(1)
            # remove the hash
            url = url.replace("#md5=%s" % md5_hash, "")
        
        # parse the archive name to find dist name and version
        archive_name = urlparse.urlparse(url)[2].split('/')[-1]
        extension_matched = False
        # remove the extension from the name
        for ext in EXTENSIONS:
            if archive_name.endswith(ext):
                archive_name = archive_name[:-len(ext)]
                extension_matched = True

        name, version = split_archive_name(archive_name)
        if extension_matched is True:
            return PyPIDistribution(name, version, url=url, md5_hash=md5_hash)

    def __init__(self, name, version, type=None, url=None, md5_hash=None):
        """Create a new instance of PyPIDistribution
        """
        self.name = name
        self.version = version
        self.url = url
        self.type = type
        self.md5_hash = md5_hash
        # set the downloaded path to Null by default. The goal here
        # is to not download distributions multiple times 
        self._downloaded_path = None

    def download(self, url=None, path=None):
        """Download the distribution to a path, and return it.

        If the path is given in path, use this, otherwise, generates a new one
        """
        if url is not None:
            self.url = url

        if path is None:
            path=tempfile.mkdtemp()
            
        # if we do not have downloaded it yet, do it.
        if self._downloaded_path is None:
            archive_name = urlparse.urlparse(self.url)[2].split('/')[-1]
            filename, headers = urllib.urlretrieve(self.url, path + "/" + archive_name)
            self._downloaded_path = filename
            self._check_md5(filename)
        return self._downloaded_path

    def _check_md5(self, filename):
        """Check that the md5 checksum of the given file matches the one in 
        self._md5_hash."""
        if self.md5_hash is not None:
            f = open(filename)
            hash = md5()
            hash.update(f.read())
            if hash.hexdigest() != self.md5_hash:
                raise MD5HashDoesNotMatch("%s instead of %s" 
                    % (hash.hexdigest(), self.md5_hash)) 

    def __repr__(self):
        return "<%s %s (%s)>" % (self.__class__.__name__, self.name, self.version)

    def _check_is_comparable(self, other):
        if not isinstance(other, PyPIDistribution):
            raise TypeError("cannot compare %s and %s" 
                % (type(self).__name__, type(other).__name__))
        elif self.name != other.name:
            raise TypeError("cannot compare %s and %s"
                % (self.name, other.name))

    def __eq__(self, other):
        self._check_is_comparable(other)
        return self.version == other.version

    def __lt__(self, other):
        self._check_is_comparable(other)
        return self.version < other.version

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        return not (self.__lt__(other) or self.__eq__(other))

    def __le__(self, other):
        return self.__eq__(other) or self.__lt__(other)

    def __ge__(self, other):
        return self.__eq__(other) or self.__gt__(other)

    # See http://docs.python.org/reference/datamodel#object.__hash__
    __hash__ = object.__hash__

class PyPIDistributions(list):
    """A container of PyPIDistribution objects.
    
    Contains methods and facilities to sort and filter distributions.
    """

    def filter(self, predicate):
        """Filter the distributions and return a subset of distributions that
        match the given predicate
        """
        return PyPIDistributions(
            [dist for dist in self if dist.name == predicate.name and
            predicate.match(dist.version)])

    def get_last(self, predicate):
        """Return the most up to date version, that satisfy the given 
        predicate
        """
        distributions = self.filter(predicate)
        distributions.sort()
        return distributions[-1]

def split_archive_name(archive_name, probable_name=None):
    """Split an archive name into two parts: name and version.

    Return the tuple (name, version)
    """
    # Try to determine wich part is the name and wich is the version using the "-"
    # separator. Take the larger part to be the version number then reduce if this
    # not works.
    def eager_split(str, maxsplit=2):
        # split using the "-" separator
        splits = str.rsplit("-", maxsplit)
        name = splits[0]
        version = "-".join(splits[1:])
        if version.startswith("-"):
            version = version[1:]
        if suggest_normalized_version(version) is None and maxsplit >= 0:
            # we dont get a good version number: recurse !
            return eager_split(str, maxsplit-1)
        else:
            return (name, version)
    if probable_name is not None:
        probable_name = probable_name.lower()
    name = None
    if probable_name is not None and probable_name in archive_name:
        # we get the name from probable_name, if given.
        name = probable_name
        version = archive_name.lstrip(name)
    else:
        name, version = eager_split(archive_name)
    
    version = suggest_normalized_version(version)
    if version != "" and name != "":
        return (name.lower(), version)
    else:
        raise CantParseArchiveName(archive_name) 
