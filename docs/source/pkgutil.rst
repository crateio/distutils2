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
      print('%s with hash %s [%d bytes] ' % (path, md5, size))
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

