import textwrap

from distutils2.tests import unittest, support
from distutils2.compat import Mixin2to3


class Mixin2to3TestCase(support.TempdirManager,
                        support.LoggingCatcher,
                        unittest.TestCase):

    #@unittest.skipIf(sys.version < '2.6', 'requires Python 2.6 or higher')
    @unittest.skipIf(True, 'Not needed for backport')
    def test_convert_code_only(self):
        # used to check if code gets converted properly.
        code = "print 'test'"

        fp = self.mktempfile()
        fp.write(code)
        fp.close()

        mixin2to3 = Mixin2to3()
        mixin2to3._run_2to3([fp.name])
        expected = "print('test')"

        fp = open(fp.name)
        converted = fp.read()
        fp.close()

        self.assertEqual(expected, converted)

    #@unittest.skipIf(sys.version < '2.6', 'requires Python 2.6 or higher')
    @unittest.skipIf(True, 'Not needed for backport')
    def test_doctests_only(self):
        # used to check if doctests gets converted properly.
        doctest = textwrap.dedent('''\
            """Example docstring.

            >>> print test
            test

            It works.
            """''')

        fp = self.mktempfile()
        fp.write(doctest)
        fp.close()

        mixin2to3 = Mixin2to3()
        mixin2to3._run_2to3([fp.name])
        expected = textwrap.dedent('''\
            """Example docstring.

            >>> print(test)
            test

            It works.
            """\n''')

        fp = open(fp.name)
        converted = fp.read()
        fp.close()

        self.assertEqual(expected, converted)

    #@unittest.skipIf(sys.version < '2.6', 'requires Python 2.6 or higher')
    @unittest.skipIf(True, 'Not needed for backport')
    def test_additional_fixers(self):
        # used to check if use_2to3_fixers works
        code = 'type(x) is not T'

        fp = self.mktempfile()
        fp.write(code)
        fp.close()

        mixin2to3 = Mixin2to3()
        mixin2to3._run_2to3(files=[fp.name], doctests=[fp.name],
                            fixers=['distutils2.tests.fixer'])

        expected = 'not isinstance(x, T)'

        fp = open(fp.name)
        converted = fp.read()
        fp.close()

        self.assertEqual(expected, converted)


def test_suite():
    return unittest.makeSuite(Mixin2to3TestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
