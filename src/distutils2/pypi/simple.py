"""pypi.simple

Contains the class "SimpleIndex" to request the PyPI "simple" index.
"""
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

from distutils2.version import VersionPredicate

from distutils2.pypi.dist import PyPIDistribution
from distutils2.pypi.errors import PyPIError


PYPI_DEFAULT_INDEX_URL = "http://pypi.python.org/simple/"

class SimpleIndex(object):
    """
    """

    def __init__(self, url=PYPI_DEFAULT_INDEX_URL, 
        hosts=('*',), ):
        """Class constructor.

        :param index_url: the url of the simple index to search on.
        :param hosts: a list of hosts allowed to be considered as internals (to
        differenciate with external hosts)
        """
        self.index_url = url
        self.allowed_hosts = hosts

    def get_distributions(self, requirements):
        """Browse the PyPI to find distributions that fullfil the given 
        requirements.

        :param requirements: A project name and it's distribution, using 
        version specifiers, as described in PEP345. 
        """
        requirements = VersionPredicate(requirements)
        self._process_package_index_page(requirements.name)

    def download(self, requirements, tmp_dir=None):
        """Download the distribution, using the requirements.

        If more than one distribution match the requirements, use the last
        version.
        Download the distribution, and put it in the tmp_dir. If no tmp_dir is
        given, creates and return one. 

        Returns the complete absolute path to the downloaded archive.
        """
        distributions = self.get_distributions(requirements)
        distribution = self._find_last_distribution(distributions)
        
        # Download logic goes here

    def _browsable(self, url):
        """Tell if the given URL needs to be browsed or not, according to the
        object internal attributes"""
        return True

    def _process_package_index_page(self, name):
        """Find and process a PyPI page for the given name.

        :param name: the name of the project to find the page
        """
        # Browse and index the content of the given PyPI page.
        # Put all informations about the processed pages in the 
        # _processed_pages attribute.
        url = self.index_url + name + "/"
        
        # Search for external links here, and process them if needed.
        # use the _browsable method to know if we can process the found links.
        for link in found_links:
            if self._browsable(link):
                self._search_in_url(link)
