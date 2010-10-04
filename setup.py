#!/usr/bin/env python
# -*- encoding: utf8 -*-
import sys
import os
import re

from distutils2 import __version__ as VERSION
from distutils2.util import find_packages
from distutils import log
from distutils.core import setup, Extension
from distutils.ccompiler import new_compiler
from distutils.command.sdist import sdist
from distutils.command.install import install

f = open('README.txt')
try:
    README = f.read()
finally:
    f.close()

def get_tip_revision(path=os.getcwd()):
    from subprocess import Popen, PIPE
    try:
        cmd = Popen(['hg', 'tip', '--template', '{rev}', '-R', path],
                    stdout=PIPE, stderr=PIPE)
    except OSError:
        return 0
    rev = cmd.stdout.read()
    if rev == '':
        # there has been an error in the command
        return 0
    return int(rev)

DEV_SUFFIX = '.dev%d' % get_tip_revision('..')


class install_hg(install):

    user_options = install.user_options + [
            ('dev', None, "Add a dev marker")
            ]

    def initialize_options(self):
        install.initialize_options(self)
        self.dev = 0

    def run(self):
        if self.dev:
            self.distribution.metadata.version += DEV_SUFFIX
        install.run(self)


class sdist_hg(sdist):

    user_options = sdist.user_options + [
            ('dev', None, "Add a dev marker")
            ]

    def initialize_options(self):
        sdist.initialize_options(self)
        self.dev = 0

    def run(self):
        if self.dev:
            self.distribution.metadata.version += DEV_SUFFIX
        sdist.run(self)


# additional paths to check, set from the command line
SSL_INCDIR = ''   # --openssl-incdir=
SSL_LIBDIR = ''   # --openssl-libdir=
SSL_DIR = ''      # --openssl-prefix=

def add_dir_to_list(dirlist, dir):
    """Add the directory 'dir' to the list 'dirlist' (at the front) if
    'dir' actually exists and is a directory.  If 'dir' is already in
    'dirlist' it is moved to the front.
    """
    if dir is not None and os.path.isdir(dir) and dir not in dirlist:
        if dir in dirlist:
            dirlist.remove(dir)
        dirlist.insert(0, dir)


def prepare_hashlib_extensions():
    """Decide which C extensions to build and create the appropriate
    Extension objects to build them.  Return a list of Extensions.
    """
    # this CCompiler object is only used to locate include files
    compiler = new_compiler()

    # Ensure that these paths are always checked
    if os.name == 'posix':
        add_dir_to_list(compiler.library_dirs, '/usr/local/lib')
        add_dir_to_list(compiler.include_dirs, '/usr/local/include')

        add_dir_to_list(compiler.library_dirs, '/usr/local/ssl/lib')
        add_dir_to_list(compiler.include_dirs, '/usr/local/ssl/include')

        add_dir_to_list(compiler.library_dirs, '/usr/contrib/ssl/lib')
        add_dir_to_list(compiler.include_dirs, '/usr/contrib/ssl/include')

        add_dir_to_list(compiler.library_dirs, '/usr/lib')
        add_dir_to_list(compiler.include_dirs, '/usr/include')

    # look in paths supplied on the command line
    if SSL_LIBDIR:
        add_dir_to_list(compiler.library_dirs, SSL_LIBDIR)
    if SSL_INCDIR:
        add_dir_to_list(compiler.include_dirs, SSL_INCDIR)
    if SSL_DIR:
        if os.name == 'nt':
            add_dir_to_list(compiler.library_dirs, os.path.join(SSL_DIR, 'out32dll'))
            # prefer the static library
            add_dir_to_list(compiler.library_dirs, os.path.join(SSL_DIR, 'out32'))
        else:
            add_dir_to_list(compiler.library_dirs, os.path.join(SSL_DIR, 'lib'))
        add_dir_to_list(compiler.include_dirs, os.path.join(SSL_DIR, 'include'))

    oslibs = {'posix': ['ssl', 'crypto'],
              'nt': ['libeay32',  'gdi32', 'advapi32', 'user32']}

    if os.name not in oslibs:
        sys.stderr.write(
            'unknown operating system, impossible to compile _hashlib')
        sys.exit(1)

    exts = []

    ssl_inc_dirs = []
    ssl_incs = []
    for inc_dir in compiler.include_dirs:
        f = os.path.join(inc_dir, 'openssl', 'ssl.h')
        if os.path.exists(f):
            ssl_incs.append(f)
            ssl_inc_dirs.append(inc_dir)

    ssl_lib = compiler.find_library_file(compiler.library_dirs, oslibs[os.name][0])

    # find out which version of OpenSSL we have
    openssl_ver = 0
    openssl_ver_re = re.compile(
        '^\s*#\s*define\s+OPENSSL_VERSION_NUMBER\s+(0x[0-9a-fA-F]+)' )
    ssl_inc_dir = ''
    for ssl_inc_dir in ssl_inc_dirs:
        name = os.path.join(ssl_inc_dir, 'openssl', 'opensslv.h')
        if os.path.isfile(name):
            try:
                incfile = open(name, 'r')
                for line in incfile:
                    m = openssl_ver_re.match(line)
                    if m:
                        openssl_ver = int(m.group(1), 16)
                        break
            except IOError:
                pass

        # first version found is what we'll use
        if openssl_ver:
            break

    if (ssl_inc_dir and ssl_lib is not None and openssl_ver >= 0x00907000):

        log.info('Using OpenSSL version 0x%08x from', openssl_ver)
        log.info(' Headers:\t%s', ssl_inc_dir)
        log.info(' Library:\t%s', ssl_lib)

        # The _hashlib module wraps optimized implementations
        # of hash functions from the OpenSSL library.
        exts.append(Extension('distutils2._backport._hashlib',
                              ['distutils2/_backport/_hashopenssl.c'],
                              include_dirs = [ssl_inc_dir],
                              library_dirs = [os.path.dirname(ssl_lib)],
                              libraries = oslibs[os.name]))
    else:
        exts.append(Extension('distutils2._backport._sha',
                              ['distutils2/_backport/shamodule.c']))
        exts.append(Extension('distutils2._backport._md5',
                              sources=['distutils2/_backport/md5module.c',
                                       'distutils2/_backport/md5.c'],
                              depends=['distutils2/_backport/md5.h']) )

    if (not ssl_lib or openssl_ver < 0x00908000):
        # OpenSSL doesn't do these until 0.9.8 so we'll bring our own
        exts.append(Extension('distutils2._backport._sha256',
                              ['distutils2/_backport/sha256module.c']))
        exts.append(Extension('distutils2._backport._sha512',
                              ['distutils2/_backport/sha512module.c']))

    return exts

setup_kwargs = {}
if sys.version < '2.6':
    setup_kwargs['scripts'] = ['distutils2/mkpkg.py']

if sys.version < '2.5':
    setup_kwargs['ext_modules'] = prepare_hashlib_extensions()

_CLASSIFIERS = """\
Development Status :: 3 - Alpha
Intended Audience :: Developers
License :: OSI Approved :: Python Software Foundation License
Operating System :: OS Independent
Programming Language :: Python
Topic :: Software Development :: Libraries :: Python Modules
Topic :: System :: Archiving :: Packaging
Topic :: System :: Systems Administration
Topic :: Utilities"""

setup(name="Distutils2",
      version=VERSION,
      description="Python Distribution Utilities",
      keywords=['packaging', 'distutils'],
      author="Tarek Ziade",
      author_email="tarek@ziade.org",
      url="http://bitbucket.org/tarek/distutils2/wiki/Home",
      license="PSF",
      long_description=README,
      classifiers=_CLASSIFIERS.split('\n'),
      packages=find_packages(),
      cmdclass={'sdist_hg': sdist_hg, 'install_hg': install_hg},
      package_data={'distutils2._backport': ['sysconfig.cfg']},
      **setup_kwargs)
