"""pypi.simple

Contains the class "SimpleIndex", a simple spider to find and retrieve
distributions on the Python Package Index, using it's "simple" API,
avalaible at http://pypi.python.org/simple/
"""
from fnmatch import translate
import urlparse
import sys
import re
import urllib2
import httplib
import socket

from distutils2.version import VersionPredicate
from distutils2.pypi.dist import PyPIDistribution, PyPIDistributions, \
    EXTENSIONS
from distutils2.pypi.errors import PyPIError, DistributionNotFound, \
    DownloadError, UnableToDownload
from distutils2 import __version__ as __distutils2_version__

# -- Constants -----------------------------------------------
PYPI_DEFAULT_INDEX_URL = "http://pypi.python.org/simple/"
PYPI_DEFAULT_MIRROR_URL = "mirrors.pypi.python.org"
DEFAULT_HOSTS = ("*",)  
SOCKET_TIMEOUT = 15
USER_AGENT = "Python-urllib/%s distutils2/%s" % (
    sys.version[:3], __distutils2_version__)

# -- Regexps -------------------------------------------------
EGG_FRAGMENT = re.compile(r'^egg=([-A-Za-z0-9_.]+)$')
HREF = re.compile("""href\\s*=\\s*['"]?([^'"> ]+)""", re.I)
PYPI_MD5 = re.compile(
    '<a href="([^"#]+)">([^<]+)</a>\n\s+\\(<a (?:title="MD5 hash"\n\s+)'
    'href="[^?]+\?:action=show_md5&amp;digest=([0-9a-f]{32})">md5</a>\\)')
URL_SCHEME = re.compile('([-+.a-z0-9]{2,}):', re.I).match

# This pattern matches a character entity reference (a decimal numeric
# references, a hexadecimal numeric reference, or a named reference).
ENTITY_SUB = re.compile(r'&(#(\d+|x[\da-fA-F]+)|[\w.:-]+);?').sub
REL = re.compile("""<([^>]*\srel\s*=\s*['"]?([^'">]+)[^>]*)>""", re.I)


def socket_timeout(timeout=SOCKET_TIMEOUT):
    """Decorator to add a socket timeout when requesting pages on PyPI.
    """
    def _socket_timeout(func):
        def _socket_timeout(self, *args, **kwargs):
            old_timeout = socket.getdefaulttimeout()
            if hasattr(self, "_timeout"):
                timeout = self._timeout
            socket.setdefaulttimeout(timeout)
            try:
                return func(self, *args, **kwargs)
            finally:
                socket.setdefaulttimeout(old_timeout)
        return _socket_timeout
    return _socket_timeout


class SimpleIndex(object):
    """Provides useful tools to request the Python Package Index simple API
    """

    def __init__(self, index_url=PYPI_DEFAULT_INDEX_URL, hosts=DEFAULT_HOSTS,
                 follow_externals=False, mirrors_url=PYPI_DEFAULT_MIRROR_URL, 
                 mirrors=None, timeout=SOCKET_TIMEOUT):
        """Class constructor.

        :param index_url: the url of the simple index to search on.
        :param hosts: a list of hosts allowed to be processed while using
                      follow_externals=True. Default behavior is to follow all 
                      hosts.
        :param follow_externals: tell if following external links is needed or 
                                 not. Default is False.
        :param mirrors_url: the url to look on for DNS records giving mirror
                            adresses.
        :param mirrors: a list of mirrors to check out if problems 
                             occurs while working with the one given in "url"
        :param timeout: time in seconds to consider a url has timeouted.
        """
        if not index_url.endswith("/"):
            index_url += "/"
        self._index_urls = [index_url]
        # if no mirrors are defined, use the method described in PEP 381.
        if mirrors is None:
            mirrors = socket.gethostbyname_ex(mirrors_url)[-1]
        self._index_urls.extend(mirrors)
        self._current_index_url = 0
        self._timeout = timeout
        self.follow_externals = follow_externals

        # create a regexp to match all given hosts
        self._allowed_hosts = re.compile('|'.join(map(translate, hosts))).match

        # we keep an index of pages we have processed, in order to avoid
        # scanning them multple time (eg. if there is multiple pages pointing
        # on one)
        self._processed_urls = []
        self._distributions = {}

    def get(self, requirements):
        """Browse the PyPI index to find distributions that fullfil the
        given requirements, and return the most recent one.
        """
        predicate = self._get_version_predicate(requirements)
        dists = self.find(predicate)

        if len(dists) == 0:
            raise DistributionNotFound(requirements)

        return dists.get_last(predicate)

    def find(self, requirements):
        """Browse the PyPI to find distributions that fullfil the given
        requirements.

        :param requirements: A project name and it's distribution, using
                             version specifiers, as described in PEP345. 
        :type requirements:  You can pass either a version.VersionPredicate 
                             or a string.
        """
        requirements = self._get_version_predicate(requirements)

        # process the index for this project
        self._process_pypi_page(requirements.name)

        # filter with requirements and return the results
        if requirements.name in self._distributions:
            dists = self._distributions[requirements.name].filter(requirements)
        else:
            dists = []

        return dists

    def download(self, requirements, temp_path=None):
        """Download the distribution, using the requirements.

        If more than one distribution match the requirements, use the last
        version.
        Download the distribution, and put it in the temp_path. If no temp_path
        is given, creates and return one.

        Returns the complete absolute path to the downloaded archive.

        :param requirements: The same as the find attribute of `find`. 
        """
        return self.get(requirements).download(path=temp_path)

    def _get_version_predicate(self, requirements):
        """Return a VersionPredicate object, from a string or an already
        existing object.
        """
        if isinstance(requirements, str):
            requirements = VersionPredicate(requirements)
        return requirements
    
    @property
    def index_url(self):
        return self._index_urls[self._current_index_url] 

    def _switch_to_next_mirror(self):
        """Switch to the next mirror (eg. point self.index_url to the next
        url.
        """
        # Internally, iter over the _index_url iterable, if we have read all
        # of the available indexes, raise an exception.
        if self._current_index_url < len(self._index_urls):
            self._current_index_url = self._current_index_url + 1
        else:
            raise UnableToDownload("All mirrors fails")
    
    def _is_browsable(self, url):
        """Tell if the given URL can be browsed or not.

        It uses the follow_externals and the hosts list to tell if the given
        url is browsable or not.
        """
        # if _index_url is contained in the given URL, we are browsing the
        # index, and it's always "browsable".
        # local files are always considered browable resources
        if self.index_url in url or urlparse.urlparse(url)[0] == "file":
            return True
        elif self.follow_externals is True:
            if self._allowed_hosts(urlparse.urlparse(url)[1]):  # 1 is netloc
                return True
            else:
                return False
        return False

    def _is_distribution(self, link):
        """Tell if the given URL matches to a distribution name or not.
        """
        #XXX find a better way to check that links are distributions
        # Using a regexp ?
        for ext in EXTENSIONS:
            if ext in link:
                return True
        return False

    def _register_dist(self, dist):
        """Register a distribution as a part of fetched distributions for
        SimpleIndex.

        Return the PyPIDistributions object for the specified project name
        """
        # Internally, check if a entry exists with the project name, if not,
        # create a new one, and if exists, add the dist to the pool.
        if not dist.name in self._distributions:
            self._distributions[dist.name] = PyPIDistributions()
        self._distributions[dist.name].append(dist)
        return self._distributions[dist.name]

    def _process_url(self, url, project_name=None, follow_links=True):
        """Process an url and search for distributions packages.

        For each URL found, if it's a download, creates a PyPIdistribution 
        object. If it's a homepage and we can follow links, process it too.

        :param url: the url to process
        :param project_name: the project name we are searching for.
        :param follow_links: Do not want to follow links more than from one
                             level. This parameter tells if we want to follow 
                             the links we find (eg. run recursively this 
                             method on it)
        """
        f = self._open_url(url)
        base_url = f.url
        if url not in self._processed_urls:
            self._processed_urls.append(url)
            link_matcher = self._get_link_matcher(url)
            for link, is_download in link_matcher(f.read(), base_url):
                if link not in self._processed_urls:
                    if self._is_distribution(link) or is_download:
                        self._processed_urls.append(link)
                        # it's a distribution, so create a dist object
                        self._register_dist(PyPIDistribution.from_url(link,
                            project_name, is_external=not self.index_url in url))
                    else:
                        if self._is_browsable(link) and follow_links:
                            self._process_url(link, project_name,
                                follow_links=False)
    
    def _get_link_matcher(self, url):
        """Returns the right link matcher function of the given url
        """
        if self.index_url in url:
            return self._simple_link_matcher
        else:
            return self._default_link_matcher

    def _simple_link_matcher(self, content, base_url):
        """Yield all links with a rel="download" or rel="homepage".

        This matches the simple index requirements for matching links.
        If follow_externals is set to False, dont yeld the external
        urls.
        """
        for match in REL.finditer(content):
            tag, rel = match.groups()
            rels = map(str.strip, rel.lower().split(','))
            if 'homepage' in rels or 'download' in rels:
                for match in HREF.finditer(tag):
                    url = urlparse.urljoin(base_url,
                                           self._htmldecode(match.group(1)))
                    if 'download' in rels or self._is_browsable(url):
                        # yield a list of (url, is_download)
                        yield (urlparse.urljoin(base_url, url), 
                               'download' in rels)

    def _default_link_matcher(self, content, base_url):
        """Yield all links found on the page.
        """
        for match in HREF.finditer(content):
            url = urlparse.urljoin(base_url, self._htmldecode(match.group(1)))
            if self._is_browsable(url):
                yield (url, False)

    def _process_pypi_page(self, name):
        """Find and process a PyPI page for the given project name.

        :param name: the name of the project to find the page
        """
        try:
            # Browse and index the content of the given PyPI page.
            url = self.index_url + name + "/"
            self._process_url(url, name)
        except DownloadError:
            # if an error occurs, try with the next index_url 
            # (provided by the mirrors)
            self._switch_to_next_mirror()
            self._distributions.clear()
            self._process_pypi_page(name)

    @socket_timeout()
    def _open_url(self, url):
        """Open a urllib2 request, handling HTTP authentication, and local
        files support.

        """
        try:
            scheme, netloc, path, params, query, frag = urlparse.urlparse(url)

            if scheme in ('http', 'https'):
                auth, host = urllib2.splituser(netloc)
            else:
                auth = None
            
            # add index.html automatically for filesystem paths
            if scheme == 'file':
                if url.endswith('/'):
                    url += "index.html"

            if auth:
                auth = "Basic " + \
                    urllib2.unquote(auth).encode('base64').strip()
                new_url = urlparse.urlunparse((
                    scheme, host, path, params, query, frag))
                request = urllib2.Request(new_url)
                request.add_header("Authorization", auth)
            else:
                request = urllib2.Request(url)
            request.add_header('User-Agent', USER_AGENT)
            fp = urllib2.urlopen(request)

            if auth:
                # Put authentication info back into request URL if same host,
                # so that links found on the page will work
                s2, h2, path2, param2, query2, frag2 = \
                    urlparse.urlparse(fp.url)
                if s2 == scheme and h2 == host:
                    fp.url = urlparse.urlunparse(
                        (s2, netloc, path2, param2, query2, frag2))

            return fp
        except (ValueError, httplib.InvalidURL), v:
            msg = ' '.join([str(arg) for arg in v.args])
            raise PyPIError('%s %s' % (url, msg))
        except urllib2.HTTPError, v:
            return v
        except urllib2.URLError, v:
            raise DownloadError("Download error for %s: %s" % (url, v.reason))
        except httplib.BadStatusLine, v:
            raise DownloadError('%s returned a bad status line. '
                'The server might be down, %s' % (url, v.line))
        except httplib.HTTPException, v:
            raise DownloadError("Download error for %s: %s" % (url, v))

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
