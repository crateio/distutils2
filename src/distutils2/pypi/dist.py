"""distutils2.pypi.dist

Provides the PyPIDistribution class thats represents a distribution retreived 
on PyPI.
"""
import re
import urlparse

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
            version = archive_name.split("-")[-1]
            name = archive_name[:-len(version)+1]
        
        if extension_matched is True:
            return PyPIDistribution(name, version, url=url, md5_hash=md5_hash)
        raise Exception("test")

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


class PyPIDistributions(list):
    """A container of PyPIDistribution objects.
    
    Contains methods and facilities to sort and filter distributions.
    """

    def filter(self, predicate):
        """Filter the distributions and return just the one matching the given
        predicate.
        """
        dists = self._distributions
        return filter(predicate.match, 
            [d.version for d in dists if d.name == predicate.name])

