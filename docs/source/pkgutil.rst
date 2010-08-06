=======
pkgutil
=======

Introduction
============

This module provides the necessary functions to provide support for
the "Importer Protocol" as described in :pep:`302` and for working with
the database of installed Python distributions which is specified in
:pep:`376`. In addition to the functions required in :pep:`376`, back support
for older ``.egg`` and ``.egg-info`` distributions is provided as well. These
distributions are represented by the class
:class:`distutils2._backport.pkgutil.EggInfoDistribution` and
most functions provide an extra argument ``use_egg_info`` which indicates if
they should consider these old styled distributions. In this document,
first a complete documentation of the functions and classes
is provided and then several use cases are presented.

Caching
+++++++

For performance purposes, the list of distributions is being internally
cached. It is enabled by default, but you can turn it off or clear
it using
:func:`distutils2._backport.pkgutil.enable_cache`,
:func:`distutils2._backport.pkgutil.disable_cache` and
:func:`distutils2._backport.pkgutil.clear_cache`.


API Reference
=============

.. automodule:: distutils2._backport.pkgutil
   :members:

Example Usage
=============

Print All Information About a Distribution
++++++++++++++++++++++++++++++++++++++++++

Given a path to a ``.dist-info`` distribution, we shall print out all
information that can be obtained using functions provided in this module::

  from distutils2._backport import pkgutil
  import sys

  path = raw_input() # read the path from the keyboard
  # first create the Distribution instance
  try:
      dist = pkgutil.Distribution(path)
  except IOError:
      print('No such distribution')
      sys.exit(1)

  print('Information about %s' % dist.name)
  print('Files')
  print('=====')
  for (path, md5, size) in dist.get_installed_files():
      print('* Path: %s' % path)
      print('  Hash %s, Size: %s bytes' % (md5, size))
  print('Metadata')
  print('========')
  for key, value in dist.metadata.items():
      print('%20s: %s' % (key, value))
  print('Extra')
  print('=====')
  if dist.requested:
      print('* It was installed by user request')
  else:
      print('* It was installed as a dependency')

If we save the script above as ``print_info.py`` and we are intested in the
distribution located at
``/home/josip/dev/distutils2/src/distutils2/_backport/tests/fake_dists/choxie-2.0.0.9``
then by typing in the console:

.. code-block:: bash

  $ echo /home/josip/dev/distutils2/src/distutils2/_backport/tests/fake_dists/choxie-2.0.0.9.dist-info | python print_info.py

we get the following output:

.. code-block:: none

  Information about choxie
  Files
  =====
  * Path: ../home/josip/dev/distutils2/src/distutils2/_backport/tests/fake_dists/choxie-2.0.0.9/truffles.py
    Hash 5e052db6a478d06bad9ae033e6bc08af, Size: 111 bytes
  * Path: ../home/josip/dev/distutils2/src/distutils2/_backport/tests/fake_dists/choxie-2.0.0.9/choxie/chocolate.py
    Hash ac56bf496d8d1d26f866235b95f31030, Size: 214 bytes
  * Path: ../home/josip/dev/distutils2/src/distutils2/_backport/tests/fake_dists/choxie-2.0.0.9/choxie/__init__.py
    Hash 416aab08dfa846f473129e89a7625bbc, Size: 25 bytes
  * Path: ../home/josip/dev/distutils2/src/distutils2/_backport/tests/fake_dists/choxie-2.0.0.9.dist-info/INSTALLER
    Hash d41d8cd98f00b204e9800998ecf8427e, Size: 0 bytes
  * Path: ../home/josip/dev/distutils2/src/distutils2/_backport/tests/fake_dists/choxie-2.0.0.9.dist-info/METADATA
    Hash 696a209967fef3c8b8f5a7bb10386385, Size: 225 bytes
  * Path: ../home/josip/dev/distutils2/src/distutils2/_backport/tests/fake_dists/choxie-2.0.0.9.dist-info/REQUESTED
    Hash d41d8cd98f00b204e9800998ecf8427e, Size: 0 bytes
  * Path: ../home/josip/dev/distutils2/src/distutils2/_backport/tests/fake_dists/choxie-2.0.0.9.dist-info/RECORD
    Hash None, Size: None bytes
  Metadata
  ========
      Metadata-Version: 1.2
                  Name: choxie
               Version: 2.0.0.9
              Platform: []
    Supported-Platform: UNKNOWN
               Summary: Chocolate with a kick!
           Description: UNKNOWN
              Keywords: []
             Home-page: UNKNOWN
                Author: UNKNOWN
          Author-email: UNKNOWN
            Maintainer: UNKNOWN
      Maintainer-email: UNKNOWN
               License: UNKNOWN
            Classifier: []
          Download-URL: UNKNOWN
        Obsoletes-Dist: ['truffles (<=0.8,>=0.5)', 'truffles (<=0.9,>=0.6)']
           Project-URL: []
         Provides-Dist: ['truffles (1.0)']
         Requires-Dist: ['towel-stuff (0.1)']
       Requires-Python: UNKNOWN
     Requires-External: []
  Extra
  =====
  * It was installed as a dependency

Find Out Obsoleted Distributions
++++++++++++++++++++++++++++++++

Now, we take tackle a different problem, we are interested in finding out
which distributions have been obsoleted. This can be easily done as follows::

  from distutils2._backport import pkgutil

  # iterate over all distributions in the system
  for dist in pkgutil.get_distributions():
      name = dist.name
      version = dist.metadata['Version']
      # find out which distributions obsolete this name/version combination
      for obsoleted_by in pkgutil.obsoletes_distribution(name, version):
          print('%s(%s) is obsoleted by %s' % (name, version, obsoleted_by.name))

This is how the output might look like:

.. code-block:: none

  strawberry(0.6) is obsoleted by choxie
  grammar(1.0a4) is obsoleted by towel-stuff

