"""Tests for the pypi.simple module.

"""
import sys
import os
import shutil
import tempfile
import unittest2
import urllib2

from distutils2.tests.pypi_server import use_pypi_server
from distutils2.pypi import simple


class PyPISimpleTestCase(unittest2.TestCase):

    def test_bad_urls(self):
        index = simple.PackageIndex()
        url = 'http://127.0.0.1:0/nonesuch/test_simple'
        try:
            v = index.open_url(url)
        except Exception, v:
            self.assertTrue(url in str(v))
        else:
            self.assertTrue(isinstance(v, urllib2.HTTPError))

        # issue 16
        # easy_install inquant.contentmirror.plone breaks because of a typo
        # in its home URL
        index = simple.PackageIndex(
            hosts=('www.example.com',))

        url = 'url:%20https://svn.plone.org/svn/collective/inquant.contentmirror.plone/trunk'
        try:
            v = index.open_url(url)
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
                v = index.open_url(url)
            except Exception, v:
                self.assertTrue('line' in str(v))
            else:
                raise AssertionError('Should have raise here!')
        finally:
            urllib2.urlopen = old_urlopen

        # issue 20
        url = 'http://http://svn.pythonpaste.org/Paste/wphp/trunk'
        try:
            index.open_url(url)
        except Exception, v:
            self.assertTrue('nonnumeric port' in str(v))

        # issue #160
        if sys.version_info[0] == 2 and sys.version_info[1] == 7:
            # this should not fail
            url = 'http://example.com'
            page = ('<a href="http://www.famfamfam.com]('
                    'http://www.famfamfam.com/">')
            index.process_index(url, page)

    def test_url_ok(self):
        index = simple.PackageIndex(
            hosts=('www.example.com',))
        url = 'file:///tmp/test_simple'
        self.assertTrue(index.url_ok(url, True))
    
    @use_pypi_server("test_found_links")
    def test_found_links(self, server):
        """Browse the index, asking for a specified distribution version
        """
        # The PyPI index contains links for version 1.0, 1.1, 2.0 and 2.0.1
        # We query only for the version 1.1, so all distributions must me
        # filled in the package_index (as the url has been scanned), but
        # obtain must only return the one we want.
        pi = simple.PackageIndex(server.full_address + "/simple/")
        last_distribution = pi.obtain(simple.Requirement.parse("foobar"))

        # we have scanned the index page
        self.assertTrue(pi.package_pages.has_key('foobar'))
        self.assertIn(server.full_address + "/simple/foobar/",
            pi.package_pages['foobar'])
        
        # we have found 4 distributions in this page
        self.assertEqual(len(pi["foobar"]), 4)

        # and returned the most recent one
        self.assertEqual(last_distribution.version, '2.0.1')

    @use_pypi_server("with_external_pages")
    def test_process_external_pages(self, server):
        """If the index provides links external to the pypi index, 
        they need to be processed, in order to discover new distributions.
        """

    @use_pypi_server()
    def test_scan_all(self, server):
        """Test that we can process the whole index and discover all related
        links.

        """
        # FIXME remove?

    @use_pypi_server("with_external_pages")
    def test_disable_external_pages(self, server):
        """Test that when we tell the simple client to not retreive external
        urls, it does well.""" 
    
    @use_pypi_server()
    def test_process_index(self, server):
        """Test that we can process a simple given string and find related links
        to distributions.
        """
    
    @use_pypi_server()
    def test_process_url(self, server):
        """Test that we can process an alternative url (not pypi related) to
        find links in it.
        """
    
    @use_pypi_server(static_filesystem_paths=["test_link_priority"],
        static_uri_paths=["simple", "external"])
    def test_links_priority(self, server):
        """
        Download links from the pypi simple index should be used before
        external download links.
        http://bitbucket.org/tarek/distribute/issue/163/md5-validation-error

        Usecase :
        - someone uploads a package on pypi, a md5 is generated
        - someone manually copies this link (with the md5 in the url) onto an
          external page accessible from the package page.
        - someone reuploads the package (with a different md5)
        - while easy_installing, an MD5 error occurs because the external link
          is used
        -> Distribute should use the link from pypi, not the external one.
        """
        # start an index server
        index_url = server.full_address + '/simple/'

        # scan a test index
        pi = simple.PackageIndex(index_url)
        requirement = simple.Requirement.parse('foobar')
        pi.find_packages(requirement)
        server.stop()

        # the distribution has been found
        self.assertTrue('foobar' in pi)
        # we have only one link, because links are compared without md5
        self.assertEqual(len(pi['foobar']), 1)
        # the link should be from the index
        self.assertTrue('correct_md5' in pi['foobar'][0].location)


def test_suite():
    return unittest2.makeSuite(PyPISimpleTestCase)

if __name__ == '__main__':
    unittest2.main(defaultTest="test_suite")
