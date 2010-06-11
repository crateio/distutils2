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

* Doing this and that::

    import sys

    # first compute a
    a = x+2
    # then print it out to stdin
    print(a)

* And that and this::

    from foo import bar

    z = lambda x,y: x^2 + y



