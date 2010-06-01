"""Tests for pypi.simple module.

"""
# More would be better!
import sys
import os
import shutil 
import tempfile 
import unittest2
import urllib2

from distutils2.tests.pypi_server import PyPIServer
from distutils2.pypi import simple

class NoneTestCase(unittest2.TestCase):
    pass

class PackageIndexTestCase(unittest2.TestCase):

    def test_bad_urls(self):
        index = simple.PackageIndex()
        url = 'http://127.0.0.1:0/nonesuch/test_simple'
        try:
            v = index.open_url(url)
        except Exception, v:
            self.assert_(url in str(v))
        else:
            self.assert_(isinstance(v,urllib2.HTTPError))

        # issue 16
        # easy_install inquant.contentmirror.plone breaks because of a typo
        # in its home URL
        index = simple.PackageIndex(
            hosts=('www.example.com',)
        )

        url = 'url:%20https://svn.plone.org/svn/collective/inquant.contentmirror.plone/trunk'
        try:
            v = index.open_url(url)
        except Exception, v:
            self.assert_(url in str(v))
        else:
            self.assert_(isinstance(v, urllib2.HTTPError))

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
                self.assert_('line' in str(v))
            else:
                raise AssertionError('Should have raise here!')
        finally:
            urllib2.urlopen = old_urlopen

        # issue 20
        url = 'http://http://svn.pythonpaste.org/Paste/wphp/trunk'
        try:
            index.open_url(url)
        except Exception, v:
            self.assert_('nonnumeric port' in str(v))

        # issue #160
        if sys.version_info[0] == 2 and sys.version_info[1] == 7:
            # this should not fail
            url = 'http://example.com'
            page = ('<a href="http://www.famfamfam.com]('
                    'http://www.famfamfam.com/">')
            index.process_index(url, page)

    def test_url_ok(self):
        index = simple.PackageIndex(
            hosts=('www.example.com',)
        )
        url = 'file:///tmp/test_simple'
        self.assert_(index.url_ok(url, True))

    def test_links_priority(self):
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
        server = PyPIServer()
        server.start()
        index_url = server.full_address + 'test_links_priority/simple/'

        # scan a test index
        pi = simple.PackageIndex(index_url)
        requirement = simple.Requirement.parse('foobar')
        pi.find_packages(requirement)
        server.stop()

        # the distribution has been found
        self.assert_('foobar' in pi)
        # we have only one link, because links are compared without md5
        self.assert_(len(pi['foobar'])==1)
        # the link should be from the index
        self.assert_('correct_md5' in pi['foobar'][0].location)

def test_suite():
    return unittest2.makeSuite(NoneTestCase)

if __name__ == '__main__':
    unittest2.main(defaultTest="test_suite")
