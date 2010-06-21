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
import httplib
import socket

from distutils2.version import VersionPredicate
from distutils2.pypi.dist import PyPIDistribution, PyPIDistributions, \
    EXTENSIONS
from distutils2.pypi.errors import PyPIError, DistributionNotFound
from distutils2 import __version__ as __distutils2_version__

# -- Constants -----------------------------------------------
PYPI_DEFAULT_INDEX_URL = "http://pypi.python.org/simple/"
DEFAULT_HOSTS = ("*.python.org",)
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


class SimpleIndex(object):
    """Provides useful tools to request the Python Package Index simple API
    """

    def __init__(self, url=PYPI_DEFAULT_INDEX_URL, hosts=DEFAULT_HOSTS,
        mirrors=[]):
        """Class constructor.

        :param index_url: the url of the simple index to search on.
        :param hosts: a list of hosts allowed to be considered as internals (to
        differenciate with external hosts)
        :param follow_externals: tell if follow external links is needed or not
        Default is False
        :param mirrors: a list of mirrors to check out if problems occurs while
        working with the one given in "url"
        """
        self.index_url = url
        self.mirrors = mirrors
        self._hosts = hosts
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
        version specifiers, as described in PEP345. You can pass either a
        version.VersionPredicate or a string.
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
        """
        requirements = self._get_version_predicate(requirements)
        distributions = self.find(requirements)
        return distributions.get_last(requirements).download(path=temp_path)

    def _get_version_predicate(self, requirements):
        """Return a VersionPredicate object, from a string or an already
        existing object.
        """
        if isinstance(requirements, str):
            requirements = VersionPredicate(requirements)
        return requirements

    def _is_browsable(self, url):
        """Tell if the given URL needs to be browsed or not, according to the
        object internal attributes.

        It uses the follow_externals and the hosts list to tell if the given
        url is browsable or not.
        """
        if self._allowed_hosts(urlparse.urlparse(url)[1]):  # 1 is netloc
            return True
        else:
            return False

    def _is_distribution(self, link):
        """Tell if the given URL matches to a distribution name or not.
        """
        #XXX find a better way to check that links are distributions
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

        :param url: the url to analyse
        :param project_name: the project name we are searching for.
        :param follow_links: We do not want to follow links more than from one
        level. This parameter tells if we want to follow the links we find (eg.
        run recursively this method on it)
        """
        f = self._open_url(url)
        base = f.url
        self._processed_urls.append(url)
        for match in HREF.finditer(f.read()):
            link = urlparse.urljoin(base, self._htmldecode(match.group(1)))
            if link not in self._processed_urls:
                if self._is_distribution(link):
                    # it's a distribution, so create a dist object
                    self._processed_urls.append(link)
                    self._register_dist(PyPIDistribution.from_url(link,
                        project_name))
                else:
                    if self._is_browsable(link) and follow_links:
                        self._process_url(link, project_name,
                            follow_links=False)

    def _process_pypi_page(self, name):
        """Find and process a PyPI page for the given project name.

        :param name: the name of the project to find the page
        """
        # Browse and index the content of the given PyPI page.
        url = self.index_url + name + "/"
        self._process_url(url, name)

    @socket_timeout()
    def _open_url(self, url):
        """Open a urllib2 request, handling HTTP authentication
        """
        try:
            scheme, netloc, path, params, query, frag = urlparse.urlparse(url)

            if scheme in ('http', 'https'):
                auth, host = urllib2.splituser(netloc)
            else:
                auth = None

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
            raise PyPIError("Download error for %s: %s" % (url, v.reason))
        except httplib.BadStatusLine, v:
            raise PyPIError('%s returned a bad status line. '
                'The server might be down, %s' % (url, v.line))
        except httplib.HTTPException, v:
            raise PyPIError("Download error for %s: %s" % (url, v))

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
