import unittest
class Loader(object):
    def loadTestsFromModule(self, names, module=None):
        class SomeTest(unittest.TestCase):
            def test_blah(self):
                self.fail("horribly")
        return unittest.makeSuite(SomeTest)
    def __repr__(self):
        return 'YO'
