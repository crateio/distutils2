"""Tests for the distutils2.pypi.dist module.
"""

from distutils2.pypi.dist import PyPIDistribution as Dist, \
    PyPIDistributions as Dists, split_archive_name
from distutils2.tests.support import unittest
from distutils2.version import VersionPredicate

class TestPyPIDistribution(unittest.TestCase):
    """tests the pypi.dist.PyPIDistribution class"""

    def test_instanciation(self):
        """Test the Distribution class provides us the good attributes when
        given on construction"""
        dist = Dist("FooBar", "1.1")
        self.assertEqual("FooBar", dist.name)
        self.assertEqual("1.1", dist.version)

    def test_from_url(self):
        """Test that the Distribution object can be built from a single URL"""
        url_list = {
            'FooBar-1.1.0.tar.gz': {
                'name': 'foobar', # lowercase the name
                'version': '1.1.0',
            },
            'Foo-Bar-1.1.0.zip': {
                'name': 'foo-bar', # keep the dash
                'version': '1.1.0',
            },
            'foobar-1.1b2.tar.gz#md5=123123123123123': {
                'name': 'foobar',
                'version': '1.1b2',
                'url':'http://test.tld/foobar-1.1b2.tar.gz', #without md5 hash
                'md5_hash': '123123123123123',
            }, 
            'foobar-1.1-rc2.tar.gz': { # use suggested name
                'name': 'foobar',
                'version': '1.1c2',
                'url':'http://test.tld/foobar-1.1-rc2.tar.gz',
            }
        }

        for url, attributes in url_list.items():
            dist = Dist.from_url("http://test.tld/"+url)
            for attribute, value in attributes.items():
                self.assertEqual(getattr(dist, attribute), value)

    def test_comparaison(self):
        """Test that we can compare PyPIDistributions"""
        foo1 = Dist("foo", "1.0")
        foo2 = Dist("foo", "2.0")
        bar = Dist("bar", "2.0")
        # assert we use the version to compare
        self.assertTrue(foo1 < foo2)
        self.assertFalse(foo1 > foo2)
        self.assertFalse(foo1 == foo2)

        # assert we can't compare dists with different names
        self.assertRaises(TypeError, foo1.__eq__,bar)

    def test_split_archive_name(self):
        """Test we can split the archive names"""
        names = {
            'foo-bar-baz-1.0-rc2': ('foo-bar-baz','1.0c2'),
            'foo-bar-baz-1.0': ('foo-bar-baz','1.0'),
            'foobarbaz-1.0': ('foobarbaz','1.0'),
        }
        for name, results in names.items():
            self.assertEqual(results, split_archive_name(name))

class TestPyPIDistributions(unittest.TestCase):
    """test the pypi.distr.PyPIDistributions class"""

    def test_filter(self):
        """Test we filter the distributions the right way, using version
        predicate match method"""
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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPyPIDistribution))
    suite.addTest(unittest.makeSuite(TestPyPIDistributions))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")
