:mod:`pkgutil` --- Package utilities
====================================

.. module:: pkgutil
   :synopsis: Utilities to support packages.

This module provides utilities to manipulate packages: support for the
Importer protocol defined in :PEP:`302` and implementation of the API
described in :PEP:`376` to work with the database of installed Python
distributions.

Import system utilities
-----------------------

.. function:: extend_path(path, name)

   Extend the search path for the modules which comprise a package.  Intended
   use is to place the following code in a package's :file:`__init__.py`::

      from pkgutil import extend_path
      __path__ = extend_path(__path__, __name__)

   This will add to the package's ``__path__`` all subdirectories of directories
   on :data:`sys.path` named after the package.  This is useful if one wants to
   distribute different parts of a single logical package as multiple
   directories.

   It also looks for :file:`\*.pkg` files beginning where ``*`` matches the
   *name* argument.  This feature is similar to :file:`\*.pth` files (see the
   :mod:`site` module for more information), except that it doesn't special-case
   lines starting with ``import``.  A :file:`\*.pkg` file is trusted at face
   value: apart from checking for duplicates, all entries found in a
   :file:`\*.pkg` file are added to the path, regardless of whether they exist
   on the filesystem.  (This is a feature.)

   If the input path is not a list (as is the case for frozen packages) it is
   returned unchanged.  The input path is not modified; an extended copy is
   returned.  Items are only appended to the copy at the end.

   It is assumed that :data:`sys.path` is a sequence.  Items of :data:`sys.path`
   that are not strings referring to existing directories are ignored. Unicode
   items on :data:`sys.path` that cause errors when used as filenames may cause
   this function to raise an exception (in line with :func:`os.path.isdir`
   behavior).


.. class:: ImpImporter(dirname=None)

   :pep:`302` Importer that wraps Python's "classic" import algorithm.

   If *dirname* is a string, a :pep:`302` importer is created that searches that
   directory.  If *dirname* is ``None``, a :pep:`302` importer is created that
   searches the current :data:`sys.path`, plus any modules that are frozen or
   built-in.

   Note that :class:`ImpImporter` does not currently support being used by
   placement on :data:`sys.meta_path`.


.. class:: ImpLoader(fullname, file, filename, etc)

   :pep:`302` Loader that wraps Python's "classic" import algorithm.


.. function:: find_loader(fullname)

   Find a :pep:`302` "loader" object for *fullname*.

   If *fullname* contains dots, path must be the containing package's
   ``__path__``.  Returns ``None`` if the module cannot be found or imported.
   This function uses :func:`iter_importers`, and is thus subject to the same
   limitations regarding platform-specific special import locations such as the
   Windows registry.


.. function:: get_importer(path_item)

   Retrieve a :pep:`302` importer for the given *path_item*.

   The returned importer is cached in :data:`sys.path_importer_cache` if it was
   newly created by a path hook.

   If there is no importer, a wrapper around the basic import machinery is
   returned.  This wrapper is never inserted into the importer cache (None is
   inserted instead).

   The cache (or part of it) can be cleared manually if a rescan of
   :data:`sys.path_hooks` is necessary.


.. function:: get_loader(module_or_name)

   Get a :pep:`302` "loader" object for *module_or_name*.

   If the module or package is accessible via the normal import mechanism, a
   wrapper around the relevant part of that machinery is returned.  Returns
   ``None`` if the module cannot be found or imported.  If the named module is
   not already imported, its containing package (if any) is imported, in order
   to establish the package ``__path__``.

   This function uses :func:`iter_importers`, and is thus subject to the same
   limitations regarding platform-specific special import locations such as the
   Windows registry.


.. function:: iter_importers(fullname='')

   Yield :pep:`302` importers for the given module name.

   If fullname contains a '.', the importers will be for the package containing
   fullname, otherwise they will be importers for :data:`sys.meta_path`,
   :data:`sys.path`, and Python's "classic" import machinery, in that order.  If
   the named module is in a package, that package is imported as a side effect
   of invoking this function.

   Non-:pep:`302` mechanisms (e.g. the Windows registry) used by the standard
   import machinery to find files in alternative locations are partially
   supported, but are searched *after* :data:`sys.path`.  Normally, these
   locations are searched *before* :data:`sys.path`, preventing :data:`sys.path`
   entries from shadowing them.

   For this to cause a visible difference in behaviour, there must be a module
   or package name that is accessible via both :data:`sys.path` and one of the
   non-:pep:`302` file system mechanisms.  In this case, the emulation will find
   the former version, while the builtin import mechanism will find the latter.

   Items of the following types can be affected by this discrepancy:
   ``imp.C_EXTENSION``, ``imp.PY_SOURCE``, ``imp.PY_COMPILED``,
   ``imp.PKG_DIRECTORY``.


.. function:: iter_modules(path=None, prefix='')

   Yields ``(module_loader, name, ispkg)`` for all submodules on *path*, or, if
   path is ``None``, all top-level modules on :data:`sys.path`.

   *path* should be either ``None`` or a list of paths to look for modules in.

   *prefix* is a string to output on the front of every module name on output.


.. function:: walk_packages(path=None, prefix='', onerror=None)

   Yields ``(module_loader, name, ispkg)`` for all modules recursively on
   *path*, or, if path is ``None``, all accessible modules.

   *path* should be either ``None`` or a list of paths to look for modules in.

   *prefix* is a string to output on the front of every module name on output.

   Note that this function must import all *packages* (*not* all modules!) on
   the given *path*, in order to access the ``__path__`` attribute to find
   submodules.

   *onerror* is a function which gets called with one argument (the name of the
   package which was being imported) if any exception occurs while trying to
   import a package.  If no *onerror* function is supplied, :exc:`ImportError`\s
   are caught and ignored, while all other exceptions are propagated,
   terminating the search.

   Examples::

      # list all modules python can access
      walk_packages()

      # list all submodules of ctypes
      walk_packages(ctypes.__path__, ctypes.__name__ + '.')


.. function:: get_data(package, resource)

   Get a resource from a package.

   This is a wrapper for the :pep:`302` loader :func:`get_data` API.  The
   *package* argument should be the name of a package, in standard module format
   (``foo.bar``).  The *resource* argument should be in the form of a relative
   filename, using ``/`` as the path separator.  The parent directory name
   ``..`` is not allowed, and nor is a rooted name (starting with a ``/``).

   The function returns a binary string that is the contents of the specified
   resource.

   For packages located in the filesystem, which have already been imported,
   this is the rough equivalent of::

      d = os.path.dirname(sys.modules[package].__file__)
      data = open(os.path.join(d, resource), 'rb').read()

   If the package cannot be located or loaded, or it uses a :pep:`302` loader
   which does not support :func:`get_data`, then ``None`` is returned.


Installed distributions database
--------------------------------

Installed Python distributions are represented by instances of
:class:`~distutils2._backport.pkgutil.Distribution`, or its subclass
:class:`~distutils2._backport.pkgutil.EggInfoDistribution` for legacy ``.egg``
and ``.egg-info`` formats).  Most functions also provide an extra argument
``use_egg_info`` to take legacy distributions into account.

.. TODO write docs here, don't rely on automodule
   classes: Distribution and descendents
   functions: provides, obsoletes, replaces, etc.

Caching
+++++++

For performance purposes, the list of distributions is being internally
cached. It is enabled by default, but you can turn it off or clear
it using :func:`~distutils2._backport.pkgutil.enable_cache`,
:func:`~distutils2._backport.pkgutil.disable_cache` and
:func:`~distutils2._backport.pkgutil.clear_cache`.


Examples
--------

Print all information about a distribution
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

Find out obsoleted distributions
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

