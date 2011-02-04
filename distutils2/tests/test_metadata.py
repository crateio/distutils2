"""Tests for distutils.metadata."""
import os
import sys
import platform
from StringIO import StringIO

from distutils2.metadata import (Metadata,
                                 PKG_INFO_PREFERRED_VERSION)
from distutils2.tests import run_unittest, unittest
from distutils2.tests.support import LoggingCatcher, WarningsCatcher
from distutils2.errors import (MetadataConflictError,
                               MetadataUnrecognizedVersionError)


class MetadataTestCase(LoggingCatcher, WarningsCatcher,
                                   unittest.TestCase):

    def test_instantiation(self):
        PKG_INFO = os.path.join(os.path.dirname(__file__), 'PKG-INFO')
        fp = open(PKG_INFO)
        try:
            contents = fp.read()
        finally:
            fp.close()
        fp = StringIO(contents)

        m = Metadata()
        self.assertRaises(MetadataUnrecognizedVersionError, m.items)

        m = Metadata(PKG_INFO)
        self.assertEqual(len(m.items()), 22)

        m = Metadata(fileobj=fp)
        self.assertEqual(len(m.items()), 22)

        m = Metadata(mapping=dict(name='Test', version='1.0'))
        self.assertEqual(len(m.items()), 11)

        d = dict(m.items())
        self.assertRaises(TypeError, Metadata,
                          PKG_INFO, fileobj=fp)
        self.assertRaises(TypeError, Metadata,
                          PKG_INFO, mapping=d)
        self.assertRaises(TypeError, Metadata,
                          fileobj=fp, mapping=d)
        self.assertRaises(TypeError, Metadata,
                          PKG_INFO, mapping=m, fileobj=fp)

    def test_metadata_read_write(self):
        PKG_INFO = os.path.join(os.path.dirname(__file__), 'PKG-INFO')
        metadata = Metadata(PKG_INFO)
        out = StringIO()
        metadata.write_file(out)
        out.seek(0)
        res = Metadata()
        res.read_file(out)
        for k in metadata.keys():
            self.assertTrue(metadata[k] == res[k])

    def test_metadata_markers(self):
        # see if we can be platform-aware
        PKG_INFO = os.path.join(os.path.dirname(__file__), 'PKG-INFO')
        content = open(PKG_INFO).read()
        content = content % sys.platform
        metadata = Metadata(platform_dependent=True)
        metadata.read_file(StringIO(content))
        self.assertEqual(metadata['Requires-Dist'], ['bar'])
        metadata['Name'] = "baz; sys.platform == 'blah'"
        # FIXME is None or 'UNKNOWN' correct here?
        # where is that documented?
        self.assertEqual(metadata['Name'], None)

        # test with context
        context = {'sys.platform': 'okook'}
        metadata = Metadata(platform_dependent=True,
                                        execution_context=context)
        metadata.read_file(StringIO(content))
        self.assertEqual(metadata['Requires-Dist'], ['foo'])

    def test_description(self):
        PKG_INFO = os.path.join(os.path.dirname(__file__), 'PKG-INFO')
        content = open(PKG_INFO).read()
        content = content % sys.platform
        metadata = Metadata()
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

    def test_mapping_api(self):
        PKG_INFO = os.path.join(os.path.dirname(__file__), 'PKG-INFO')
        content = open(PKG_INFO).read()
        content = content % sys.platform
        metadata = Metadata(fileobj=StringIO(content))
        self.assertIn('Version', metadata.keys())
        self.assertIn('0.5', metadata.values())
        self.assertIn(('Version', '0.5'), metadata.items())

        metadata.update({'version': '0.6'})
        self.assertEqual(metadata['Version'], '0.6')
        metadata.update([('version', '0.7')])
        self.assertEqual(metadata['Version'], '0.7')

    def test_versions(self):
        metadata = Metadata()
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

    # XXX Spurious Warnings were disabled
    def XXXtest_warnings(self):
        metadata = Metadata()

        # these should raise a warning
        values = (('Requires-Dist', 'Funky (Groovie)'),
                  ('Requires-Python', '1-4'))

        for name, value in values:
            metadata.set(name, value)

        # we should have a certain amount of warnings
        self.assertEqual(len(self.logs), 2)

    def test_multiple_predicates(self):
        metadata = Metadata()

        # see for "3" instead of "3.0"  ???
        # its seems like the MINOR VERSION can be omitted
        metadata['Requires-Python'] = '>=2.6, <3.0'
        metadata['Requires-Dist'] = ['Foo (>=2.6, <3.0)']

        self.assertEqual(len(self.warnings), 0)

    def test_project_url(self):
        metadata = Metadata()
        metadata['Project-URL'] = [('one', 'http://ok')]
        self.assertEqual(metadata['Project-URL'],
                          [('one', 'http://ok')])
        self.assertEqual(metadata.version, '1.2')

    def test_check_version(self):
        metadata = Metadata()
        metadata['Name'] = 'vimpdb'
        metadata['Home-page'] = 'http://pypi.python.org'
        metadata['Author'] = 'Monty Python'
        metadata.docutils_support = False
        missing, warnings = metadata.check()
        self.assertEqual(missing, ['Version'])

    def test_check_version_strict(self):
        metadata = Metadata()
        metadata['Name'] = 'vimpdb'
        metadata['Home-page'] = 'http://pypi.python.org'
        metadata['Author'] = 'Monty Python'
        metadata.docutils_support = False
        from distutils2.errors import MetadataMissingError
        self.assertRaises(MetadataMissingError, metadata.check, strict=True)

    def test_check_name(self):
        metadata = Metadata()
        metadata['Version'] = '1.0'
        metadata['Home-page'] = 'http://pypi.python.org'
        metadata['Author'] = 'Monty Python'
        metadata.docutils_support = False
        missing, warnings = metadata.check()
        self.assertEqual(missing, ['Name'])

    def test_check_name_strict(self):
        metadata = Metadata()
        metadata['Version'] = '1.0'
        metadata['Home-page'] = 'http://pypi.python.org'
        metadata['Author'] = 'Monty Python'
        metadata.docutils_support = False
        from distutils2.errors import MetadataMissingError
        self.assertRaises(MetadataMissingError, metadata.check, strict=True)

    def test_check_author(self):
        metadata = Metadata()
        metadata['Version'] = '1.0'
        metadata['Name'] = 'vimpdb'
        metadata['Home-page'] = 'http://pypi.python.org'
        metadata.docutils_support = False
        missing, warnings = metadata.check()
        self.assertEqual(missing, ['Author'])

    def test_check_homepage(self):
        metadata = Metadata()
        metadata['Version'] = '1.0'
        metadata['Name'] = 'vimpdb'
        metadata['Author'] = 'Monty Python'
        metadata.docutils_support = False
        missing, warnings = metadata.check()
        self.assertEqual(missing, ['Home-page'])

    def test_check_predicates(self):
        metadata = Metadata()
        metadata['Version'] = 'rr'
        metadata['Name'] = 'vimpdb'
        metadata['Home-page'] = 'http://pypi.python.org'
        metadata['Author'] = 'Monty Python'
        metadata['Requires-dist'] = ['Foo (a)']
        metadata['Obsoletes-dist'] = ['Foo (a)']
        metadata['Provides-dist'] = ['Foo (a)']
        if metadata.docutils_support:
            missing, warnings = metadata.check()
            self.assertEqual(len(warnings), 4)
            metadata.docutils_support = False
        missing, warnings = metadata.check()
        self.assertEqual(len(warnings), 4)

    def test_best_choice(self):
        metadata = Metadata()
        metadata['Version'] = '1.0'
        self.assertEqual(metadata.version, PKG_INFO_PREFERRED_VERSION)
        metadata['Classifier'] = ['ok']
        self.assertEqual(metadata.version, '1.2')

    def test_project_urls(self):
        # project-url is a bit specific, make sure we write it
        # properly in PKG-INFO
        metadata = Metadata()
        metadata['Version'] = '1.0'
        metadata['Project-Url'] = [('one', 'http://ok')]
        self.assertEqual(metadata['Project-Url'], [('one', 'http://ok')])
        file_ = StringIO()
        metadata.write_file(file_)
        file_.seek(0)
        res = file_.read().split('\n')
        self.assertIn('Project-URL: one,http://ok', res)

        file_.seek(0)
        metadata = Metadata()
        metadata.read_file(file_)
        self.assertEqual(metadata['Project-Url'], [('one', 'http://ok')])


def test_suite():
    return unittest.makeSuite(MetadataTestCase)

if __name__ == '__main__':
    run_unittest(test_suite())
