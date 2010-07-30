"""Tests for distutils.command.bdist."""
import os
import sys
import tempfile
from StringIO import StringIO

from distutils2.metadata import (DistributionMetadata, _interpret,
                                 PKG_INFO_PREFERRED_VERSION)
from distutils2.tests.support import unittest, LoggingSilencer
from distutils2.errors import (MetadataConflictError,
                               MetadataUnrecognizedVersionError)

class DistributionMetadataTestCase(LoggingSilencer, unittest.TestCase):


    def test_interpret(self):
        platform = sys.platform
        version = sys.version.split()[0]
        os_name = os.name

        self.assertTrue(_interpret("sys.platform == '%s'" % platform))
        self.assertTrue(_interpret(
            "sys.platform == '%s' or python_version == '2.4'" % platform))
        self.assertTrue(_interpret(
            "sys.platform == '%s' and python_full_version == '%s'" %
            (platform, version)))
        self.assertTrue(_interpret("'%s' == sys.platform" % platform))

        self.assertTrue(_interpret('os.name == "%s"' % os_name))

        # stuff that need to raise a syntax error
        ops = ('os.name == os.name', 'os.name == 2', "'2' == '2'",
               'okpjonon', '', 'os.name ==')
        for op in ops:
            self.assertRaises(SyntaxError, _interpret, op)

        # combined operations
        OP = 'os.name == "%s"' % os_name
        AND = ' and '
        OR = ' or '
        self.assertTrue(_interpret(OP + AND + OP))
        self.assertTrue(_interpret(OP + AND + OP + AND + OP))
        self.assertTrue(_interpret(OP + OR + OP))
        self.assertTrue(_interpret(OP + OR + OP + OR + OP))

        # other operators
        self.assertTrue(_interpret("os.name != 'buuuu'"))
        self.assertTrue(_interpret("python_version > '1.0'"))
        self.assertTrue(_interpret("python_version < '5.0'"))
        self.assertTrue(_interpret("python_version <= '5.0'"))
        self.assertTrue(_interpret("python_version >= '1.0'"))
        self.assertTrue(_interpret("'%s' in os.name" % os_name))
        self.assertTrue(_interpret("'buuuu' not in os.name"))
        self.assertTrue(_interpret(
            "'buuuu' not in os.name and '%s' in os.name" % os_name))

        # execution context
        self.assertTrue(_interpret('python_version == "0.1"',
                                   {'python_version': '0.1'}))

    def test_metadata_read_write(self):

        PKG_INFO = os.path.join(os.path.dirname(__file__), 'PKG-INFO')
        metadata = DistributionMetadata(PKG_INFO)
        res = tempfile.NamedTemporaryFile()
        metadata.write_file(res)
        res.flush()
        res = DistributionMetadata(res.name)
        for k in metadata.keys():
            self.assertTrue(metadata[k] == res[k])

    def test_metadata_markers(self):
        # see if we can be platform-aware
        PKG_INFO = os.path.join(os.path.dirname(__file__), 'PKG-INFO')
        content = open(PKG_INFO).read()
        content = content % sys.platform
        metadata = DistributionMetadata(platform_dependent=True)
        metadata.read_file(StringIO(content))
        self.assertEqual(metadata['Requires-Dist'], ['bar'])

        # test with context
        context = {'sys.platform': 'okook'}
        metadata = DistributionMetadata(platform_dependent=True,
                                        execution_context=context)
        metadata.read_file(StringIO(content))
        self.assertEqual(metadata['Requires-Dist'], ['foo'])

    def test_description(self):
        PKG_INFO = os.path.join(os.path.dirname(__file__), 'PKG-INFO')
        content = open(PKG_INFO).read()
        content = content % sys.platform
        metadata = DistributionMetadata()
        metadata.read_file(StringIO(content))

        # see if we can read the description now
        DESC = os.path.join(os.path.dirname(__file__), 'LONG_DESC.txt')
        wanted = open(DESC).read()
        self.assertEqual(wanted, metadata['Description'])

        # save the file somewhere and make sure we can read it back
        out = StringIO()
        metadata.write_file(out)
        out.seek(0)
        metadata.read_file(out)
        self.assertEqual(wanted, metadata['Description'])

    def test_mapper_apis(self):
        PKG_INFO = os.path.join(os.path.dirname(__file__), 'PKG-INFO')
        content = open(PKG_INFO).read()
        content = content % sys.platform
        metadata = DistributionMetadata()
        metadata.read_file(StringIO(content))
        self.assertIn('Version', metadata.keys())
        self.assertIn('0.5', metadata.values())
        self.assertIn(('Version', '0.5'), metadata.items())

    def test_versions(self):
        metadata = DistributionMetadata()
        metadata['Obsoletes'] = 'ok'
        self.assertEqual(metadata['Metadata-Version'], '1.1')

        del metadata['Obsoletes']
        metadata['Obsoletes-Dist'] = 'ok'
        self.assertEqual(metadata['Metadata-Version'], '1.2')

        self.assertRaises(MetadataConflictError, metadata.set,
                          'Obsoletes', 'ok')

        del metadata['Obsoletes']
        del metadata['Obsoletes-Dist']
        metadata['Version'] = '1'
        self.assertEqual(metadata['Metadata-Version'], '1.0')

        PKG_INFO = os.path.join(os.path.dirname(__file__),
                                'SETUPTOOLS-PKG-INFO')
        metadata.read_file(StringIO(open(PKG_INFO).read()))
        self.assertEqual(metadata['Metadata-Version'], '1.0')

        PKG_INFO = os.path.join(os.path.dirname(__file__),
                                'SETUPTOOLS-PKG-INFO2')
        metadata.read_file(StringIO(open(PKG_INFO).read()))
        self.assertEqual(metadata['Metadata-Version'], '1.1')

        metadata.version = '1.618'
        self.assertRaises(MetadataUnrecognizedVersionError, metadata.keys)

    def test_warnings(self):
        metadata = DistributionMetadata()

        # these should raise a warning
        values = (('Requires-Dist', 'Funky (Groovie)'),
                  ('Requires-Python', '1-4'))

        from distutils2 import metadata as m
        old = m.warn
        m.warns = 0

        def _warn(*args):
            m.warns += 1

        m.warn = _warn

        try:
            for name, value in values:
                metadata.set(name, value)
        finally:
            m.warn = old
            res = m.warns
            del m.warns

        # we should have a certain amount of warnings
        num_wanted = len(values)
        self.assertEqual(num_wanted, res)

    def test_multiple_predicates(self):
        metadata = DistributionMetadata()

        from distutils2 import metadata as m
        old = m.warn
        m.warns = 0

        def _warn(*args):
            m.warns += 1

        # see for "3" instead of "3.0"  ???
        # its seems like the MINOR VERSION can be omitted
        m.warn = _warn
        try:
            metadata['Requires-Python'] = '>=2.6, <3.0'
            metadata['Requires-Dist'] = ['Foo (>=2.6, <3.0)']
        finally:
            m.warn = old
            res = m.warns
            del m.warns

        self.assertEqual(res, 0)

    def test_project_url(self):
        metadata = DistributionMetadata()
        metadata['Project-URL'] = [('one', 'http://ok')]
        self.assertEqual(metadata['Project-URL'],
                          [('one', 'http://ok')])
        self.assertEqual(metadata.version, '1.2')

    def test_check(self):
        metadata = DistributionMetadata()
        metadata['Version'] = 'rr'
        metadata['Requires-dist'] = ['Foo (a)']
        missing, warnings = metadata.check()
        self.assertEqual(missing, ['Name', 'Home-page'])
        self.assertEqual(len(warnings), 2)

    def test_best_choice(self):
        metadata = DistributionMetadata()
        metadata['Version'] = '1.0'
        self.assertEqual(metadata.version, PKG_INFO_PREFERRED_VERSION)
        metadata['Classifier'] = ['ok']
        self.assertEqual(metadata.version, '1.2')

    def test_project_urls(self):
        # project-url is a bit specific, make sure we write it
        # properly in PKG-INFO
        metadata = DistributionMetadata()
        metadata['Version'] = '1.0'
        metadata['Project-Url'] = [('one', 'http://ok')]
        self.assertEqual(metadata['Project-Url'], [('one', 'http://ok')])
        file_ = StringIO()
        metadata.write_file(file_)
        file_.seek(0)
        res = file_.read().split('\n')
        self.assertIn('Project-URL: one,http://ok', res)

        file_.seek(0)
        metadata = DistributionMetadata()
        metadata.read_file(file_)
        self.assertEqual(metadata['Project-Url'], [('one', 'http://ok')])


def test_suite():
    return unittest.makeSuite(DistributionMetadataTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
