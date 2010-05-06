#!/usr/bin/env python
# -*- encoding: utf8 -*-
__revision__ = "$Id$"
import sys
import os

from distutils2.core import setup
from distutils2.command.sdist import sdist
from distutils2.command.install import install
from distutils2 import __version__ as VERSION
from distutils2.util import find_packages

f = open('README.txt')
try:
    README = f.read()
finally:
    f.close()

def get_tip_revision(path=os.getcwd()):
    try:
        from mercurial.hg import repository
        from mercurial.ui import ui
        from mercurial import node
        from mercurial.error import RepoError
    except ImportError:
        return 0
    try:
        repo = repository(ui(), path)
        tip = repo.changelog.tip()
        return repo.changelog.rev(tip)
    except RepoError:
        return 0

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

setup_kwargs = {}
if sys.version < '2.6':
    setup_kwargs['scripts'] = ['distutils2/mkpkg.py']

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

setup (name="Distutils2",
       version=VERSION,
       summary="Python Distribution Utilities",
       keywords=['packaging', 'distutils'],
       author="Tarek Ziade",
       author_email="tarek@ziade.org",
       home_page="http://bitbucket.org/tarek/distutils2/wiki/Home",
       license="PSF",
       description=README,
       classifier=_CLASSIFIERS.split('\n'),
       packages=find_packages(),
       cmdclass={'sdist': sdist_hg, 'install': install_hg},
       package_data={'distutils2._backport': ['sysconfig.cfg']},
       project_url=[('Mailing-list',
                    'http://mail.python.org/mailman/listinfo/distutils-sig/'),
                    ('Documentation',
                     'http://packages.python.org/distutils2'),
                    ('Repository', 'http://hg.python.org/distutils2'),
                    ('Bug tracker', 'http://bugs.python.org')],
       **setup_kwargs
       )


