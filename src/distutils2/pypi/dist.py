"""distutils2.pypi.dist

Provides the PyPIDistribution class thats represents a distribution retreived 
on PyPI.
"""
import re
import urlparse

from distutils2.version import suggest_normalized_version 

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
        archive_name = urlparse.urlparse(url).path.split('/')[-1]
        extension_matched = False
        # remove the extension from the name
        for ext in EXTENSIONS:
            if archive_name.endswith(ext):
                archive_name = archive_name[:-len(ext)]
                extension_matched = True

        name = None
        # get the name from probable_dist_name
        if probable_dist_name is not None:
            if probable_dist_name in archive_name:
                name = probable_dist_name

        if name is None:
            # determine the name and the version
            splits = archive_name.split("-")
            version = splits[-1]
            name = "-".join(splits[:-1])
        else:
            # just determine the version
            version = archive_name[len(name):]
            if version.startswith("-"):
                version = version[1:]
        
        version = suggest_normalized_version(version)
        if extension_matched is True:
            return PyPIDistribution(name, version, url=url, md5_hash=md5_hash)

    def __init__(self, name, version, type=None, url=None, md5_hash=None):
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

        # if we do not have downloaded it yet, do it.
        if self._downloaded_path is None:
            # download logic goes here
            real_path = "" 
        return real_path

    def __str__(self):
        """string representation of the PyPIDistribution"""
        return "%s-%s" % (self.name, self.version)


class PyPIDistributions(list):
    """A container of PyPIDistribution objects.
    
    Contains methods and facilities to sort and filter distributions.
    """

    def filter(self, predicate):
        """Filter the distributions and return just the one matching the given
        predicate.
        """
        return [dist for dist in self if dist.name == predicate.name and
            predicate.match(dist.version)]

