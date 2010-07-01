"""distutils2.pypi.dist

Provides the PyPIDistribution class thats represents a distribution retrieved
on PyPI.
"""
import re
import urlparse
import urllib
import tempfile
try:
    import hashlib
except ImportError:
    from distutils2._backport import hashlib

from distutils2.version import suggest_normalized_version
from distutils2.pypi.errors import HashDoesNotMatch, UnsupportedHashName

EXTENSIONS = ".tar.gz .tar.bz2 .tar .zip .tgz .egg".split()
MD5_HASH = re.compile(r'^.*#md5=([a-f0-9]+)$')


class PyPIDistribution(object):
    """Represents a distribution retrieved from PyPI.

    This is a simple container for various attributes as name, version,
    location, url etc.

    The PyPIDistribution class is used by the pypi.*Index class to return
    information about distributions.
    """

    @classmethod
    def from_url(cls, url, probable_dist_name=None, is_external=True):
        """Build a Distribution from a url archive (egg or zip or tgz).

        :param url: complete url of the distribution
        :param probable_dist_name: A probable name of the distribution. 
        :param is_external: Tell if the url commes from an index or from 
                            an external URL.
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
            return PyPIDistribution(name, version, url=url, hashname="md5", 
                                    hashval=md5_hash, is_external=is_external)

    def __init__(self, name, version, type=None, url=None, hashname=None, 
                 hashval=None, is_external=True):
        """Create a new instance of PyPIDistribution.

        :param name: the name of the distribution
        :param version: the version of the distribution
        :param type: the type of the dist (eg. source, bin-*, etc.)
        :param url: URL where we found this distribution
        :param hashname: the name of the hash we want to use. Refer to the
                         hashlib.new documentation for more information.
        :param hashval: the hash value.
        :param is_external: we need to know if the provided url comes from an 
                            index browsing, or from an external resource.

        """
        self.name = name
        self.version = version
        self.type = type
        # set the downloaded path to None by default. The goal here
        # is to not download distributions multiple times
        self.location = None
        # We store urls in dict, because we need to have a bit more informations
        # than the simple URL. It will be used later to find the good url to
        # use.
        # We have two _url* attributes: _url and _urls. _urls contains a list of 
        # dict for the different urls, and _url contains the choosen url, in 
        # order to dont make the selection process multiple times.
        self._urls = []
        self._url = None
        self.add_url(url, hashname, hashval, is_external)
    
    def add_url(self, url, hashname=None, hashval=None, is_external=True):
        """Add a new url to the list of urls"""
        if hashname is not None:
            try:
                hashlib.new(hashname)
            except ValueError:
                raise UnsupportedHashName(hashname)

        self._urls.append({
            'url': url,
            'hashname': hashname,
            'hashval': hashval,
            'is_external': is_external,
        })
        # reset the url selection process
        self._url = None

    @property
    def url(self):
        """Pick up the right url for the list of urls in self.urls"""
        # We return internal urls over externals.
        # If there is more than one internal or external, return the first
        # one.
        if self._url is None:
            if len(self._urls) > 1:
                internals_urls = [u for u in self._urls \
                                  if u['is_external'] == False]
                if len(internals_urls) >= 1: 
                    self._url = internals_urls[0]
            if self._url is None:
                self._url = self._urls[0]
        return self._url

    def download(self, path=None):
        """Download the distribution to a path, and return it.

        If the path is given in path, use this, otherwise, generates a new one
        """
        if path is None:
            path = tempfile.mkdtemp()

        # if we do not have downloaded it yet, do it.
        if self.location is None:
            url = self.url['url']
            archive_name = urlparse.urlparse(url)[2].split('/')[-1]
            filename, headers = urllib.urlretrieve(url, 
                                                   path + "/" + archive_name)
            self.location = filename
            self._check_md5(filename)
        return self.location

    def _check_md5(self, filename):
        """Check that the md5 checksum of the given file matches the one in
        url param"""
        hashname = self.url['hashname']
        expected_hashval = self.url['hashval']
        if not None in (expected_hashval, hashname):
            f = open(filename)
            hashval = hashlib.new(hashname)
            hashval.update(f.read())
            if hashval.hexdigest() != expected_hashval:
                raise HashDoesNotMatch("got %s instead of %s"
                    % (hashval.hexdigest(), expected_hashval))

    def __repr__(self):
        return "<%s %s (%s)>" \
            % (self.__class__.__name__, self.name, self.version)

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
    def __init__(self, list=[]):
        # To disable the ability to pass lists on instanciation
        super(PyPIDistributions, self).__init__()
        for item in list:
            self.append(item)

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

    def append(self, o):
        """Append a new distribution to the list.
        
        If a distribution with the same name and version exists, just grab the
        URL informations and add a new new url for the existing one.
        """
        similar_dists = [d for d in self if d.name == o.name and
                         d.version == o.version]
        if len(similar_dists) > 0:
            dist = similar_dists[0]
            dist.add_url(**o.url)
        else:
            super(PyPIDistributions, self).append(o)
        

def split_archive_name(archive_name, probable_name=None):
    """Split an archive name into two parts: name and version.

    Return the tuple (name, version)
    """
    # Try to determine wich part is the name and wich is the version using the
    # "-" separator. Take the larger part to be the version number then reduce
    # if this not works.
    def eager_split(str, maxsplit=2):
        # split using the "-" separator
        splits = str.rsplit("-", maxsplit)
        name = splits[0]
        version = "-".join(splits[1:])
        if version.startswith("-"):
            version = version[1:]
        if suggest_normalized_version(version) is None and maxsplit >= 0:
            # we dont get a good version number: recurse !
            return eager_split(str, maxsplit - 1)
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
