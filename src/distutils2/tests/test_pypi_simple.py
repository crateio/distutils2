"""Tests for the pypi.simple module.

"""
import sys
import os
import shutil
import tempfile
import urllib2

from distutils2.tests import support
from distutils2.tests.support import unittest
from distutils2.tests.pypi_server import use_pypi_server, PyPIServer, \
                                         PYPI_DEFAULT_STATIC_PATH
from distutils2.pypi import simple

from distutils2.errors import DistutilsError


class PyPISimpleTestCase(support.TempdirManager,
                         unittest.TestCase):

    def _get_simple_index(self, server, base_url="/simple/", hosts=None,
        *args, **kwargs):
        """Build and return a SimpleSimpleIndex instance, with the test server
        urls
        """
        if hosts is None:
            hosts = (server.full_address.strip("http://"),)
        kwargs['hosts'] = hosts
        return simple.SimpleIndex(server.full_address + base_url, *args,
            **kwargs)

    def test_bad_urls(self):
        index = simple.SimpleIndex()
        url = 'http://127.0.0.1:0/nonesuch/test_simple'
        try:
            v = index._open_url(url)
        except Exception, v:
            self.assertTrue(url in str(v))
        else:
            self.assertTrue(isinstance(v, urllib2.HTTPError))

        # issue 16
        # easy_install inquant.contentmirror.plone breaks because of a typo
        # in its home URL
        index = simple.SimpleIndex(
            hosts=('www.example.com',))

        url = 'url:%20https://svn.plone.org/svn/collective/inquant.contentmirror.plone/trunk'
        try:
            v = index._open_url(url)
        except Exception, v:
            self.assertTrue(url in str(v))
        else:
            self.assertTrue(isinstance(v, urllib2.HTTPError))

        def _urlopen(*args):
            import httplib
            raise httplib.BadStatusLine('line')

        old_urlopen = urllib2.urlopen
        urllib2.urlopen = _urlopen
        url = 'http://example.com'
        try:
            try:
                v = index._open_url(url)
            except Exception, v:
                self.assertTrue('line' in str(v))
            else:
                raise AssertionError('Should have raise here!')
        finally:
            urllib2.urlopen = old_urlopen

        # issue 20
        url = 'http://http://svn.pythonpaste.org/Paste/wphp/trunk'
        try:
            index._open_url(url)
        except Exception, v:
            self.assertTrue('nonnumeric port' in str(v))

        # issue #160
        if sys.version_info[0] == 2 and sys.version_info[1] == 7:
            # this should not fail
            url = 'http://example.com'
            page = ('<a href="http://www.famfamfam.com]('
                    'http://www.famfamfam.com/">')
            index.process_index(url, page)

    @use_pypi_server("test_found_links")
    def test_found_links(self, server):
        """Browse the index, asking for a specified distribution version
        """
        # The PyPI index contains links for version 1.0, 1.1, 2.0 and 2.0.1
        index = self._get_simple_index(server)
        last_distribution = index.get("foobar")

        # we have scanned the index page
        self.assertIn(server.full_address + "/simple/foobar/",
            index._processed_urls)

        # we have found 4 distributions in this page
        self.assertEqual(len(index._distributions["foobar"]), 4)

        # and returned the most recent one
        self.assertEqual("%s" % last_distribution.version, '2.0.1')

    def test_is_browsable(self):
        index = simple.SimpleIndex(follow_externals=False)
        self.assertTrue(index._is_browsable(index.index_url + "test"))

        # Now, when following externals, we can have a list of hosts to trust.
        # and don't follow other external links than the one described here.
        index = simple.SimpleIndex(hosts=["pypi.python.org", "test.org"],
                                   follow_externals=True)
        good_urls = (
            "http://pypi.python.org/foo/bar",
            "http://pypi.python.org/simple/foobar",
            "http://test.org",
            "http://test.org/",
            "http://test.org/simple/",
        )
        bad_urls = (
            "http://python.org",
            "http://test.tld",
        )

        for url in good_urls:
            self.assertTrue(index._is_browsable(url))

        for url in bad_urls:
            self.assertFalse(index._is_browsable(url))

        # allow all hosts
        index = simple.SimpleIndex(follow_externals=True, hosts=("*",))
        self.assertTrue(index._is_browsable("http://an-external.link/path"))
        self.assertTrue(index._is_browsable("pypi.test.tld/a/path"))

        # specify a list of hosts we want to allow
        index = simple.SimpleIndex(follow_externals=True,
                                   hosts=("*.test.tld",))
        self.assertFalse(index._is_browsable("http://an-external.link/path"))
        self.assertTrue(index._is_browsable("http://pypi.test.tld/a/path"))

    @use_pypi_server("with_externals")
    def test_restrict_hosts(self, server):
        """Include external pages
        """
        # Try to request the package index, wich contains links to "externals"
        # resources. They have to  be scanned too.
        index = self._get_simple_index(server, follow_externals=True)
        index.get("foobar")
        self.assertIn(server.full_address + "/external/external.html",
            index._processed_urls)

    @use_pypi_server("with_real_externals")
    def test_restrict_hosts(self, server):
        """Only use a list of allowed hosts is possible
        """
        # Test that telling the simple pyPI client to not retrieve external
        # works
        index = self._get_simple_index(server, follow_externals=False)
        index.get("foobar")
        self.assertNotIn(server.full_address + "/external/external.html",
            index._processed_urls)

    @use_pypi_server("with_egg_files")
    def test_scan_egg_files(self, server):
        """Assert that egg files are indexed as well"""
        pass

    @use_pypi_server(static_filesystem_paths=["with_externals"],
        static_uri_paths=["simple", "external"])
    def test_links_priority(self, server):
        """
        Download links from the pypi simple index should be used before
        external download links.
        http://bitbucket.org/tarek/distribute/issue/163/md5-validation-error

        Usecase :
        - someone uploads a package on pypi, a md5 is generated
        - someone manually coindexes this link (with the md5 in the url) onto
          an external page accessible from the package page.
        - someone reuploads the package (with a different md5)
        - while easy_installing, an MD5 error occurs because the external link
          is used
        -> The index should use the link from pypi, not the external one.
        """
        # start an index server
        index_url = server.full_address + '/simple/'

        # scan a test index
        index = simple.SimpleIndex(index_url, follow_externals=True)
        dists = index.find("foobar")
        server.stop()

        # we have only one link, because links are compared without md5
        self.assertEqual(len(dists), 1)
        # the link should be from the index
        self.assertEqual('12345678901234567', dists[0].url['hashval'])
        self.assertEqual('md5', dists[0].url['hashname'])

    @use_pypi_server(static_filesystem_paths=["with_norel_links"],
        static_uri_paths=["simple", "external"])
    def test_not_scan_all_links(self, server):
        """Do not follow all index page links.
        The links not tagged with rel="download" and rel="homepage" have
        to not be processed by the package index, while processing "pages".
        """
        # process the pages
        index = self._get_simple_index(server, follow_externals=True)
        index.find("foobar")
        # now it should have processed only pages with links rel="download"
        # and rel="homepage"
        self.assertIn("%s/simple/foobar/" % server.full_address,
            index._processed_urls)  # it's the simple index page
        self.assertIn("%s/external/homepage.html" % server.full_address,
            index._processed_urls)  # the external homepage is rel="homepage"
        self.assertNotIn("%s/external/nonrel.html" % server.full_address,
            index._processed_urls)  # this link contains no rel=*
        self.assertNotIn("%s/unrelated-0.2.tar.gz" % server.full_address,
            index._processed_urls)  # linked from simple index (no rel)
        self.assertIn("%s/foobar-0.1.tar.gz" % server.full_address,
            index._processed_urls)  # linked from simple index (rel)
        self.assertIn("%s/foobar-2.0.tar.gz" % server.full_address,
            index._processed_urls)  # linked from external homepage (rel)

    def test_uses_mirrors(self):
        """When the main repository seems down, try using the given mirrors"""
        server = PyPIServer("foo_bar_baz")
        mirror = PyPIServer("foo_bar_baz")
        mirror.start()  # we dont start the server here

        try:
            # create the index using both servers
            index = simple.SimpleIndex(server.full_address + "/simple/",
                hosts=('*',), timeout=1,  # set the timeout to 1s for the tests
                mirrors=[mirror.full_address + "/simple/",])

            # this should not raise a timeout
            self.assertEqual(4, len(index.find("foo")))
        finally:
            mirror.stop()

    def test_simple_link_matcher(self):
        """Test that the simple link matcher yields the right links"""
        index = simple.SimpleIndex(follow_externals=False)

        # Here, we define:
        #   1. one link that must be followed, cause it's a download one
        #   2. one link that must *not* be followed, cause the is_browsable
        #      returns false for it.
        #   3. one link that must be followed cause it's a homepage that is
        #      browsable
        self.assertTrue(index._is_browsable("%stest" % index.index_url))
        self.assertFalse(index._is_browsable("http://dl-link2"))
        content = """
        <a href="http://dl-link1" rel="download">download_link1</a>
        <a href="http://dl-link2" rel="homepage">homepage_link1</a>
        <a href="%stest" rel="homepage">homepage_link2</a>
        """ % index.index_url

        # Test that the simple link matcher yield the good links.
        generator = index._simple_link_matcher(content, index.index_url)
        self.assertEqual(('http://dl-link1', True), generator.next())
        self.assertEqual(('%stest' % index.index_url, False),
                         generator.next())
        self.assertRaises(StopIteration, generator.next)

        # Follow the external links is possible
        index.follow_externals = True
        generator = index._simple_link_matcher(content, index.index_url)
        self.assertEqual(('http://dl-link1', True), generator.next())
        self.assertEqual(('http://dl-link2', False), generator.next())
        self.assertEqual(('%stest' % index.index_url, False),
                         generator.next())
        self.assertRaises(StopIteration, generator.next)

    def test_browse_local_files(self):
        """Test that we can browse local files"""
        index_path = os.sep.join(["file://" + PYPI_DEFAULT_STATIC_PATH,
                                  "test_found_links", "simple"])
        index = simple.SimpleIndex(index_path)
        dists = index.find("foobar")
        self.assertEqual(4, len(dists))

def test_suite():
    return unittest.makeSuite(PyPISimpleTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
