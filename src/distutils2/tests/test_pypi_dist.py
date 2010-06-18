"""Tests for the distutils2.pypi.dist module.
"""

from distutils2.pypi.dist import PyPIDistribution, PyPIDistributions
from distutils2.tests.support import unittest
from distutils2.version import VersionPredicate

class TestPyPIDistribution(unittest.TestCase):
    """tests the pypi.dist.PyPIDistribution class"""

    def test_instanciation(self):
        """Test the Distribution class provides us the good attributes when
        given on construction"""
        dist = PyPIDistribution("FooBar", "1.1")
        self.assertEqual("FooBar", dist.name)
        self.assertEqual("1.1", dist.version)

    def test_from_url(self):
        """Test that the Distribution object can be built from a single URL"""
        url_list = {
            'FooBar-1.1.0.tar.gz': {
                'name': 'FooBar',
                'version': '1.1.0',
            },
            'Foo-Bar-1.1.0.zip': {
                'name': 'Foo-Bar',
                'version': '1.1.0',
            },
            'foobar-1.1b2.tar.gz#md5=123123123123123': {
                'name': 'foobar',
                'version': '1.1b2',
                'url':'http://test.tld/foobar-1.1b2.tar.gz', #without md5 hash
                'md5_hash': '123123123123123',
            }
        }

        for url, attributes in url_list.items():
            dist = PyPIDistribution.from_url("http://test.tld/"+url)
            for attribute, value in attributes.items():
                self.assertEqual(getattr(dist, attribute), value) 

class TestPyPIDistributions(unittest.TestCase):
    """test the pypi.distr.PyPIDistributions class"""

    def test_filter(self):
        """Test we filter the distributions the right way, using version
        predicate match method"""
        dists = PyPIDistributions((
            PyPIDistribution("FooBar", "1.1"),
            PyPIDistribution("FooBar", "1.1.1"),
            PyPIDistribution("FooBar", "1.2"),
            PyPIDistribution("FooBar", "1.2.1"),
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
