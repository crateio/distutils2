"""pypi.simple

Contains the class "SimpleIndex", a simple spider to find and retreive 
distributions on the Python Package Index, using it's "simple" API, 
avalaible at http://pypi.python.org/simple/
"""
from fnmatch import translate
import urlparse
import sys
import re
import urllib2
import socket
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

from distutils2.version import VersionPredicate
from distutils2.pypi.dist import PyPIDistribution, EXTENSIONS
from distutils2.pypi.errors import PyPIError
from distutils2 import __version__ as __distutils2_version__

# -- Constants -----------------------------------------------
PYPI_DEFAULT_INDEX_URL = "http://pypi.python.org/simple/"
SOCKET_TIMEOUT=15
USER_AGENT = "Python-urllib/%s distutils2/%s" % (
    sys.version[:3], __distutils2_version__
)

# -- Regexps -------------------------------------------------
EGG_FRAGMENT = re.compile(r'^egg=([-A-Za-z0-9_.]+)$')
HREF = re.compile("""href\\s*=\\s*['"]?([^'"> ]+)""", re.I)
PYPI_MD5 = re.compile(
    '<a href="([^"#]+)">([^<]+)</a>\n\s+\\(<a (?:title="MD5 hash"\n\s+)'
    'href="[^?]+\?:action=show_md5&amp;digest=([0-9a-f]{32})">md5</a>\\)'
)
URL_SCHEME = re.compile('([-+.a-z0-9]{2,}):',re.I).match
# This pattern matches a character entity reference (a decimal numeric
# references, a hexadecimal numeric reference, or a named reference).
ENTITY_SUB = re.compile(r'&(#(\d+|x[\da-fA-F]+)|[\w.:-]+);?').sub

def socket_timeout(timeout=SOCKET_TIMEOUT):
    """Decorator to add a socket timeout when requesting pages on PyPI.
    """
    def _socket_timeout(func):
        def _socket_timeout(*args, **kwargs):
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(timeout)
            try:
                return func(*args, **kwargs)
            finally:
                socket.setdefaulttimeout(old_timeout)
        return _socket_timeout
    return _socket_timeout


class UrlProcessor(object):
    """Tools to process urls and return links from them.
    """
    def __init__(self):
        self._processed_urls = {}

    def find_links(self, url, is_browsable=lambda x:True):
        """Find links and return them, for a specific url.
        
        Use "is_browsable" to provides a method to tell if the found urls might
        be browsed or not.
        """
        pass


class SimpleIndex(object):
    """Provides useful tools to request the Python Package Index simple API
    """

    def __init__(self, url=PYPI_DEFAULT_INDEX_URL, 
        hosts=('*',), follow_externals=False):
        """Class constructor.

        :param index_url: the url of the simple index to search on.
        :param hosts: a list of hosts allowed to be considered as internals (to
        differenciate with external hosts)
        :param follow_externals: tell if follow external links is needed or not
        Default is False
        """
        self.index_url = url
        self.follow_externals=follow_externals
         
        # create a regexp to match all given hosts
        self._allowed_hosts = re.compile('|'.join(map(translate,hosts))).match

        # _current_requirements are used to know what the index is currently
        # browsing for. This could be used to determine the distributon name
        # while having multiple ambigous names/version couples
        self._current_requirements = None
        self._processed_pages = []

    def get_distributions(self, requirements):
        """Browse the PyPI to find distributions that fullfil the given 
        requirements.

        :param requirements: A project name and it's distribution, using 
        version specifiers, as described in PEP345. 
        """
        requirements = VersionPredicate(requirements)
        self.current_requirements = requirements
        
        # process the index for this project
        distributions = self._process_pypi_page(requirements.name)
        
        # filter with requirements and return the results
        return distributions.filter(requirements)

    def download(self, requirements, temp_path=None):
        """Download the distribution, using the requirements.

        If more than one distribution match the requirements, use the last
        version.
        Download the distribution, and put it in the temp_path. If no temp_path 
        is given, creates and return one. 

        Returns the complete absolute path to the downloaded archive.
        """
        distributions = self.get_distributions(requirements)
        return distributions.get_last(requirements) \
            .download(temp_path=temp_path)

    def _is_browsable(self, url):
        """Tell if the given URL needs to be browsed or not, according to the
        object internal attributes.

        It uses the follow_externals and the hosts list to tell if the given 
        url is browsable or not. 
        """
        if self.follow_externals is True:
            return True
        return True if self._allowed_hosts(urlparse(url).netloc) else False

    def _is_distribution(self, link):
        """Tell if the given URL matches to a distribution name or not.
        """
         

    def _process_url(self, url):
        """Process an url and return fetched links.
        """
        f = self._open_url(url)
        base = f.url
        for match in HREF.finditer(f.read()):
            link = urlparse.urljoin(base, self._htmldecode(match.group(1)))
            if self._is_distribution(link):
                PyPIDistribution.from_url(link)
            else:

    def _process_pypi_page(self, name):
        """Find and process a PyPI page for the given project name.

        :param name: the name of the project to find the page
        """
        # Browse and index the content of the given PyPI page.
        # Put all informations about the processed pages in the 
        # _processed_pages attribute.
        url = self.index_url + name + "/"
        found_links = self._process_url(url)
        
        # Search for external links here, and process them if needed.
        for link in found_links:
            if self._is_browsable(link):
                self._search_in_url(link)
    
    @socket_timeout()
    def _open_url(self, url):
        """Open a urllib2 request, handling HTTP authentication
        """
        scheme, netloc, path, params, query, frag = urlparse.urlparse(url)

        if scheme in ('http', 'https'):
            auth, host = urllib2.splituser(netloc)
        else:
            auth = None

        if auth:
            auth = "Basic " + urllib2.unquote(auth).encode('base64').strip()
            new_url = urlparse.urlunparse((scheme,host,path,params,query,frag))
            request = urllib2.Request(new_url)
            request.add_header("Authorization", auth)
        else:
            request = urllib2.Request(url)

        request.add_header('User-Agent', USER_AGENT)
        fp = urllib2.urlopen(request)

        if auth:
            # Put authentication info back into request URL if same host,
            # so that links found on the page will work
            s2, h2, path2, param2, query2, frag2 = urlparse.urlparse(fp.url)
            if s2==scheme and h2==host:
                fp.url = urlparse.urlunparse((s2,netloc,path2,param2,query2,frag2))

        return fp

    def _decode_entity(self, match):
        what = match.group(1)
        if what.startswith('#x'):
            what = int(what[2:], 16)
        elif what.startswith('#'):
            what = int(what[1:])
        else:
            from htmlentitydefs import name2codepoint
            what = name2codepoint.get(what, match.group(0))
        return unichr(what)

    def _htmldecode(self, text):
        """Decode HTML entities in the given text."""
        return ENTITY_SUB(self._decode_entity, text)
