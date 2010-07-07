"""Tests for the distutils2.pypi.dist module."""

import os
import shutil
import tempfile

from distutils2.tests.pypi_server import use_pypi_server
from distutils2.tests import support
from distutils2.tests.support import unittest
from distutils2.version import VersionPredicate
from distutils2.pypi.errors import HashDoesNotMatch, UnsupportedHashName
from distutils2.pypi.dist import (PyPIDistribution as Dist,
                                  PyPIDistributions as Dists,
                                  split_archive_name, create_from_url)


class TestPyPIDistribution(support.TempdirManager,
                           unittest.TestCase):
    """Tests the pypi.dist.PyPIDistribution class"""

    def test_instanciation(self):
        # Test the Distribution class provides us the good attributes when
        # given on construction
        dist = Dist("FooBar", "1.1")
        self.assertEqual("FooBar", dist.name)
        self.assertEqual("1.1", "%s" % dist.version)

    def test_create_from_url(self):
        # Test that the Distribution object can be built from a single URL
        url_list = {
            'FooBar-1.1.0.tar.gz': {
                'name': 'foobar',  # lowercase the name
                'version': '1.1',
            },
            'Foo-Bar-1.1.0.zip': {
                'name': 'foo-bar',  # keep the dash
                'version': '1.1',
            },
            'foobar-1.1b2.tar.gz#md5=123123123123123': {
                'name': 'foobar',
                'version': '1.1b2',
                'url': {
                    'url': 'http://test.tld/foobar-1.1b2.tar.gz',  # no hash
                    'hashval': '123123123123123',
                    'hashname': 'md5',
                }
            },
            'foobar-1.1-rc2.tar.gz': {  # use suggested name
                'name': 'foobar',
                'version': '1.1c2',
                'url': {
                    'url': 'http://test.tld/foobar-1.1-rc2.tar.gz',
                }
            }
        }

        for url, attributes in url_list.items():
            dist = create_from_url("http://test.tld/" + url)
            for attribute, value in attributes.items():
                if isinstance(value, dict):
                    mylist = getattr(dist, attribute)
                    for val in value.keys():
                        self.assertEqual(value[val], mylist[val])
                else:
                    if attribute == "version":
                        self.assertEqual("%s" % getattr(dist, "version"), value)
                    else:
                        self.assertEqual(getattr(dist, attribute), value)

    def test_get_url(self):
        # Test that the url property works well

        d = Dist("foobar", "1.1", url="test_url")
        self.assertDictEqual(d.url, {
            "url": "test_url",
            "is_external": True,
            "hashname": None,
            "hashval": None,
        })

        # add a new url
        d.add_url(url="internal_url", is_external=False)
        self.assertEqual(d._url, None)
        self.assertDictEqual(d.url, {
            "url": "internal_url",
            "is_external": False,
            "hashname": None,
            "hashval": None,
        })
        self.assertEqual(2, len(d._urls))

    def test_comparaison(self):
        # Test that we can compare PyPIDistributions
        foo1 = Dist("foo", "1.0")
        foo2 = Dist("foo", "2.0")
        bar = Dist("bar", "2.0")
        # assert we use the version to compare
        self.assertTrue(foo1 < foo2)
        self.assertFalse(foo1 > foo2)
        self.assertFalse(foo1 == foo2)

        # assert we can't compare dists with different names
        self.assertRaises(TypeError, foo1.__eq__, bar)

    def test_split_archive_name(self):
        # Test we can split the archive names
        names = {
            'foo-bar-baz-1.0-rc2': ('foo-bar-baz', '1.0c2'),
            'foo-bar-baz-1.0': ('foo-bar-baz', '1.0'),
            'foobarbaz-1.0': ('foobarbaz', '1.0'),
        }
        for name, results in names.items():
            self.assertEqual(results, split_archive_name(name))

    @use_pypi_server("downloads_with_md5")
    def test_download(self, server):
        # Download is possible, and the md5 is checked if given

        url = "%s/simple/foobar/foobar-0.1.tar.gz" % server.full_address
        # check md5 if given
        dist = Dist("FooBar", "0.1", url=url,
            url_hashname="md5", url_hashval="d41d8cd98f00b204e9800998ecf8427e")
        dist.download()

        # a wrong md5 fails
        dist2 = Dist("FooBar", "0.1", url=url,
            url_hashname="md5", url_hashval="wrongmd5")
        self.assertRaises(HashDoesNotMatch, dist2.download)

        # we can omit the md5 hash
        dist3 = Dist("FooBar", "0.1", url=url)
        dist3.download()

        # and specify a temporary location
        # for an already downloaded dist
        path1 = tempfile.mkdtemp()
        dist3.download(path=path1)
        # and for a new one
        path2_base = tempfile.mkdtemp()
        dist4 = Dist("FooBar", "0.1", url=url)
        path2 = dist4.download(path=path2_base)
        self.assertTrue(path2_base in path2)

        # remove the temp folders
        shutil.rmtree(path1)
        shutil.rmtree(os.path.dirname(path2))

    def test_hashname(self):
        # Invalid hashnames raises an exception on assignation
        Dist("FooBar", "0.1", url_hashname="md5", url_hashval="value")

        self.assertRaises(UnsupportedHashName, Dist, "FooBar", "0.1",
                          url_hashname="invalid_hashname", url_hashval="value")


class TestPyPIDistributions(unittest.TestCase):

    def test_filter(self):
        # Test we filter the distributions the right way, using version
        # predicate match method
        dists = Dists((
            Dist("FooBar", "1.1"),
            Dist("FooBar", "1.1.1"),
            Dist("FooBar", "1.2"),
            Dist("FooBar", "1.2.1"),
        ))
        filtered = dists.filter(VersionPredicate("FooBar (<1.2)"))
        self.assertNotIn(dists[2], filtered)
        self.assertNotIn(dists[3], filtered)
        self.assertIn(dists[0], filtered)
        self.assertIn(dists[1], filtered)

    def test_append(self):
        # When adding a new item to the list, the behavior is to test if
        # a distribution with the same name and version number already exists,
        # and if so, to add url informations to the existing PyPIDistribution
        # object.
        # If no object matches, just add "normally" the object to the list.

        dists = Dists([
            Dist("FooBar", "1.1", url="external_url", type="source"),
        ])
        self.assertEqual(1, len(dists))
        dists.append(Dist("FooBar", "1.1", url="internal_url",
                          url_is_external=False, type="source"))
        self.assertEqual(1, len(dists))
        self.assertEqual(2, len(dists[0]._urls))

        dists.append(Dist("Foobar", "1.1.1", type="source"))
        self.assertEqual(2, len(dists))

        # when adding a distribution whith a different type, a new distribution
        # has to be added.
        dists.append(Dist("Foobar", "1.1.1", type="binary"))
        self.assertEqual(3, len(dists))

    def test_prefer_final(self):
        # Can order the distributions using prefer_final

        fb10 = Dist("FooBar", "1.0")  # final distribution
        fb11a = Dist("FooBar", "1.1a1")  # alpha
        fb12a = Dist("FooBar", "1.2a1")  # alpha
        fb12b = Dist("FooBar", "1.2b1")  # beta
        dists = Dists([fb10, fb11a, fb12a, fb12b])

        dists.sort_distributions(prefer_final=True)
        self.assertEqual(fb10, dists[0])

        dists.sort_distributions(prefer_final=False)
        self.assertEqual(fb12b, dists[0])

    def test_prefer_source(self):
        # Ordering support prefer_source
        fb_source = Dist("FooBar", "1.0", type="source")
        fb_binary = Dist("FooBar", "1.0", type="binary")
        fb2_binary = Dist("FooBar", "2.0", type="binary")
        dists = Dists([fb_binary, fb_source])

        dists.sort_distributions(prefer_source=True)
        self.assertEqual(fb_source, dists[0])

        dists.sort_distributions(prefer_source=False)
        self.assertEqual(fb_binary, dists[0])

        dists.append(fb2_binary)
        dists.sort_distributions(prefer_source=True)
        self.assertEqual(fb2_binary, dists[0])

    def test_get_same_name_and_version(self):
        # PyPIDistributions can return a list of "duplicates"
        fb_source = Dist("FooBar", "1.0", type="source")
        fb_binary = Dist("FooBar", "1.0", type="binary")
        fb2_binary = Dist("FooBar", "2.0", type="binary")
        dists = Dists([fb_binary, fb_source, fb2_binary])
        duplicates = dists.get_same_name_and_version()
        self.assertTrue(1, len(duplicates))
        self.assertIn(fb_source, duplicates[0])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPyPIDistribution))
    suite.addTest(unittest.makeSuite(TestPyPIDistributions))
    return suite

if __name__ == '__main__':
    run_unittest(test_suite())
