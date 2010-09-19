# -*- encoding: utf-8 -*-
import sys
import os
from distutils2.core import setup, Extension
from distutils2.errors import CCompilerError, DistutilsError, CompileError
from distutils2.command.build_ext import build_ext as distutils_build_ext

VERSION = "0.1"

class build_ext(distutils_build_ext):

    def build_extension(self, ext):
        try:
            return distutils_build_ext.build_extension(self, ext)
        except (CCompilerError, DistutilsError, CompileError), e:
            pass

def _get_ext_modules():
    levenshtein = Extension('_levenshtein',
                            sources=[os.path.join('texttools',
                                                  '_levenshtein.c')])
    return [levenshtein]

with open('README.txt') as f:
    LONG_DESCRIPTION = f.read()

setup(name="TextTools", version=VERSION, author="Tarek Ziade",
      author_email="tarek@ziade.org",
      home_page="http://bitbucket.org/tarek/texttools",
      summary="Text manipulation utilities",
      description=LONG_DESCRIPTION,
      keywords="text,guess,levenshtein",
      classifiers=[
         'Development Status :: 4 - Beta',
         'Intended Audience :: Developers',
         'License :: OSI Approved :: Python Software Foundation License'
      ],
      cmdclass={'build_ext': build_ext},
      packages=['texttools'],
      package_dir={'texttools': 'texttools'},
      package_data={'texttools': [os.path.join('samples', '*.txt')]},
      scripts=[os.path.join('scripts', 'levenshtein.py'),
               os.path.join('scripts', 'guesslang.py')],
      ext_modules=_get_ext_modules()
      )

