:mod:`distutils2` --- Packaging support
=======================================

.. module:: distutils2
   :synopsis: Packaging system and building blocks for other packaging systems
.. sectionauthor:: Distutils2 contributors


The :mod:`distutils2` package provides support for building, packaging,
distributing and installing additional projects into a Python installation.
Projects may be include modules, extension modules, packages and scripts.
:mod:`distutils2` also provides building blocks for other packaging systems
that do not use the command system.

This manual is the reference documentation for those standalone building
blocks and for extending Distutils2. If you're looking for the user-centric
guides to install a project or package your own code, head to `See also`__.


.. toctree::
    :maxdepth: 2
    :numbered:

    distutils2.version
    distutils2.metadata
    distutils2.depgraph
    distutils2.index
    distutils2.tests.pypi_server


.. __:

.. seealso::

   :doc:`../distutils/index`
      The manual for developers of Python projects who want to package and
      distribute them. This describes how to use :mod:`distutils2` to make
      projects easily found and added to an existing Python installation.

   :doc:`../install/index`
      A user-centered manual which includes information on adding projects
      into an existing Python installation.  You do not need to be a Python
      programmer to read this manual.
