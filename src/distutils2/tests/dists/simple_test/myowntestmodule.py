import unittest
class SomeTest(unittest.TestCase):
    def test_blah(self):
        self.fail("horribly")
def test_suite():
    return unittest.makeSuite(SomeTest)
