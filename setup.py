#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import os
import re
import sys
import codecs
from distutils import sysconfig
from distutils.core import setup, Extension
from distutils.ccompiler import new_compiler
try:
    from configparser import RawConfigParser
except ImportError: #<3.0
    from ConfigParser import RawConfigParser

def cfg_to_args(path='setup.cfg'):
    from distutils2.util import split_multiline
    def split_elements(value):
        return [ v.strip() for v in value.split(',') ]
    def split_files(value):
        return [ str(v) for v in split_multiline(value) ]
    opts_to_args =  {
        'metadata': (
            ('name', 'name', None),
            ('version', 'version', None),
            ('author', 'author', None),
            ('author-email', 'author_email', None),
            ('maintainer', 'maintainer', None),
            ('maintainer-email', 'maintainer_email', None),
            ('home-page', 'url', None),
            ('summary', 'description', None),
            ('description', 'long_description', None),
            ('download-url', 'download_url', None),
            ('classifier', 'classifiers', split_multiline),
            ('platform', 'platforms', split_multiline),
            ('license', 'license', None),
            ('keywords', 'keywords', split_elements),
            ),
        'files': (
            ('packages', 'packages', split_files),
            ('modules', 'py_modules', split_files),
            ('scripts', 'scripts', split_files),
            ('package_data', 'package_data', split_files),
            ),
        }
    config = RawConfigParser()
    config.optionxform = lambda x: x.lower().replace('_', '-')
    fp = codecs.open(path, encoding='utf-8')
    try:
        config.readfp(fp)
    finally:
        fp.close()
    kwargs = {}
    for section in opts_to_args:
        for optname, argname, xform in opts_to_args[section]:
            if config.has_option(section, optname):
                value = config.get(section, optname)
                if xform:
                    value = xform(value)
                kwargs[argname] = value
    # Handle `description-file`
    if ('long_description' not in kwargs and
            config.has_option('metadata', 'description-file')):
        filenames = config.get('metadata', 'description-file')
        for filename in split_multiline(filenames):
            descriptions = []
            fp = open(filename)
            try:
                descriptions.append(fp.read())
            finally:
                fp.close()
        kwargs['long_description'] = '\n\n'.join(descriptions)
    # Handle `package_data`
    if 'package_data' in kwargs:
        package_data = {}
        for data in kwargs['package_data']:
            key, value = data.split('=', 1)
            globs = package_data.setdefault(key.strip(), [])
            globs.extend(split_elements(value))
        kwargs['package_data'] = package_data
    return kwargs

# (from Python's setup.py, in PyBuildExt.detect_modules())
def prepare_hashlib_extensions():
    """Decide which C extensions to build and create the appropriate
    Extension objects to build them.  Return a list of Extensions.
    """
    ssl_libs = None
    ssl_inc_dir = None
    ssl_lib_dirs = []
    ssl_inc_dirs = []
    if os.name == 'posix':
        # (from Python's setup.py, in PyBuildExt.detect_modules())
        # lib_dirs and inc_dirs are used to search for files;
        # if a file is found in one of those directories, it can
        # be assumed that no additional -I,-L directives are needed.
        lib_dirs = []
        inc_dirs = []
        if os.path.normpath(sys.prefix) != '/usr':
            lib_dirs.append(sysconfig.get_config_var('LIBDIR'))
            inc_dirs.append(sysconfig.get_config_var('INCLUDEDIR'))
        # Ensure that /usr/local is always used
        lib_dirs.append('/usr/local/lib')
        inc_dirs.append('/usr/local/include')
        # Add the compiler defaults; this compiler object is only used
        # to locate the OpenSSL files.
        compiler = new_compiler()
        lib_dirs.extend(compiler.library_dirs)
        inc_dirs.extend(compiler.include_dirs)
        # Now the platform defaults
        lib_dirs.extend(['/lib64', '/usr/lib64', '/lib', '/usr/lib'])
        inc_dirs.extend(['/usr/include'])
        # Find the SSL library directory
        ssl_libs = ['ssl', 'crypto']
        ssl_lib = compiler.find_library_file(lib_dirs, 'ssl')
        if ssl_lib is None:
            ssl_lib_dirs = ['/usr/local/ssl/lib', '/usr/contrib/ssl/lib']
            ssl_lib = compiler.find_library_file(ssl_lib_dirs, 'ssl')
            if ssl_lib is not None:
                ssl_lib_dirs.append(os.path.dirname(ssl_lib))
            else:
                ssl_libs = None
        # Locate the SSL headers
        for ssl_inc_dir in inc_dirs + ['/usr/local/ssl/include',
                                       '/usr/contrib/ssl/include']:
            ssl_h = os.path.join(ssl_inc_dir, 'openssl', 'ssl.h')
            if os.path.exists(ssl_h):
                if ssl_inc_dir not in inc_dirs:
                    ssl_inc_dirs.append(ssl_inc_dir)
                break
    elif os.name == 'nt':
        # (from Python's PCbuild/build_ssl.py, in find_best_ssl_dir())
        # Look for SSL 1 level up from here.  That is, the same place the
        # other externals for Python core live.
        # note: do not abspath src_dir; the build will fail if any
        # higher up directory name has spaces in it.
        src_dir = '..'
        try:
            fnames = os.listdir(src_dir)
        except OSError:
            fnames = []
        ssl_dir = None
        best_parts = []
        for fname in fnames:
            fqn = os.path.join(src_dir, fname)
            if os.path.isdir(fqn) and fname.startswith("openssl-"):
                # We have a candidate, determine the best
                parts = re.split("[.-]", fname)[1:]
                # Ignore all "beta" or any other qualifiers;
                # eg - openssl-0.9.7-beta1
                if len(parts) < 4 and parts > best_parts:
                    best_parts = parts
                    ssl_dir = fqn
        if ssl_dir is not None:
            ssl_libs = ['gdi32', 'user32', 'advapi32',
                        os.path.join(ssl_dir, 'out32', 'libeay32')]
            ssl_inc_dir = os.path.join(ssl_dir, 'inc32')
            ssl_inc_dirs.append(ssl_inc_dir)

    # Find out which version of OpenSSL we have
    openssl_ver = 0
    openssl_ver_re = re.compile(
        '^\s*#\s*define\s+OPENSSL_VERSION_NUMBER\s+(0x[0-9a-fA-F]+)' )
    if ssl_inc_dir is not None:
        opensslv_h = os.path.join(ssl_inc_dir, 'openssl', 'opensslv.h')
        try:
            incfile = open(opensslv_h, 'r')
            for line in incfile:
                m = openssl_ver_re.match(line)
                if m:
                    openssl_ver = int(m.group(1), 16)
        except IOError:
            e = str(sys.last_value)
            print("IOError while reading %s: %s" % (opensslv_h, e))

    # Now we can determine which extension modules need to be built.
    exts = []
    if ssl_libs is not None and openssl_ver >= 0x907000:
        # The _hashlib module wraps optimized implementations
        # of hash functions from the OpenSSL library.
        exts.append(Extension('distutils2._backport._hashlib',
                              ['distutils2/_backport/_hashopenssl.c'],
                              include_dirs=ssl_inc_dirs,
                              library_dirs=ssl_lib_dirs,
                              libraries=ssl_libs))
    else:
        # no openssl at all, use our own md5 and sha1
        exts.append(Extension('distutils2._backport._sha',
                              ['distutils2/_backport/shamodule.c']))
        exts.append(Extension('distutils2._backport._md5',
                              sources=['distutils2/_backport/md5module.c',
                                       'distutils2/_backport/md5.c'],
                              depends=['distutils2/_backport/md5.h']) )
    if openssl_ver < 0x908000:
        # OpenSSL doesn't do these until 0.9.8 so we'll bring our own
        exts.append(Extension('distutils2._backport._sha256',
                              ['distutils2/_backport/sha256module.c']))
        exts.append(Extension('distutils2._backport._sha512',
                              ['distutils2/_backport/sha512module.c']))
    return exts

setup_kwargs = cfg_to_args('setup.cfg')
if sys.version < '2.5':
    setup_kwargs['ext_modules'] = prepare_hashlib_extensions()
setup(**setup_kwargs)
