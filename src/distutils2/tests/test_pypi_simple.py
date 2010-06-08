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

from distutils2.errors import DistutilsError

class PyPISimpleTestCase(unittest2.TestCase):

    def _get_simple_package_index(self, server, base_url="/simple/", *args,
            **kwargs):
        """Build and return a SimpleSimpleIndex instance, with the test server
        urls
        """
        return simple.SimpleIndex(server.full_address + base_url, *args,
            **kwargs)

    def test_bad_urls(self):
        index = simple.SimpleIndex()
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
        index = simple.SimpleIndex(
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
        index = simple.SimpleIndex(
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
        pi = self._get_simple_package_index(server)
        last_distribution = pi.obtain(simple.Requirement.parse("foobar"))

        # we have scanned the index page
        self.assertTrue(pi.package_pages.has_key('foobar'))
        self.assertIn(server.full_address + "/simple/foobar/",
            pi.package_pages['foobar'])
        
        # we have found 4 distributions in this page
        self.assertEqual(len(pi["foobar"]), 4)

        # and returned the most recent one
        self.assertEqual(last_distribution.version, '2.0.1')

    @use_pypi_server("with_externals")
    def test_process_external_pages(self, server):
        """Include external pages in obtain process
        """
        # Try to request the package index, wich contains links to "externals"
        # resources. They have to  be scanned too.
        pi = self._get_simple_package_index(server, follow_externals=True)
        pi.obtain(simple.Requirement.parse("foobar"))
        self.assertIn(server.full_address + "/external/external.html",
            pi.scanned_urls.keys())

    @use_pypi_server("with_real_externals")
    def test_disable_external_pages(self, server):
        """Exclude external pages if disabled 
        """
        # Test that telling the simple pyPI client to not retreive external
        # works
        pi = self._get_simple_package_index(server, follow_externals=False)
        pi.obtain(simple.Requirement.parse("foobar"))
        self.assertNotIn(server.full_address + "/external/external.html",
            pi.scanned_urls.keys())

    @use_pypi_server("downloads_with_md5")
    def test_download_package(self, server):
        """Download packages from pypi requests.
        """
        paths = []
        # If we request a download specific version of a distribution, 
        # the system must download it, check the md5 and unpack it in a 
        # temporary location, that must be returned by the lib.
        pi = self._get_simple_package_index(server)

        # assert we can download a specific version
        temp_location_1 = pi.download(
            simple.Requirement.parse("foobar == 0.1"))
        self.assertIn("foobar-0.1.tar.gz", temp_location_1)
        paths.append(temp_location_1)
        
        # assert we take the latest
        temp_location_2 = pi.download(simple.Requirement.parse("foobar"))
        self.assertIn("foobar-0.1.tar.gz", temp_location_2)
        paths.append(temp_location_2)

        # we also can specify a temp location
        specific_temp_location = tempfile.mkdtemp()
        returned_temp_location = pi.download(
            simple.Requirement.parse("foobar"), 
            tmpdir=specific_temp_location)
        self.assertIn(specific_temp_location, returned_temp_location)
        paths.append(returned_temp_location)

        # raise an error if we couldnt manage to get the file with a the good
        # md5 hash
        self.assertRaises(DistutilsError, pi.download,
            simple.Requirement.parse("badmd5"))
        # XXX: is this making sense ? do file on pypi can have a wrong md5 
        # hash ?
        # If the pypi package index contain a file with the wrong md5, try to
        # use the external locations to retreive it.
        # in the test, the "wrongmd5" project contain a bad version of the
        # archive, but a external site contains the good one. We want to use the
        # external one to retreive the file with the good md5.
        # if we really can't manage to get the right md5, raise an exception
        
        for path in paths:
            shutil.rmtree(os.path.dirname(path))

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
        pi = simple.SimpleIndex(index_url)
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
