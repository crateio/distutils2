===============================
Dependency Graph Builder Module
===============================

Introduction
------------

This module provides the means to create a graph of dependencies from a list
of :class:`distutils2._backport.pkgutil.Distribution` and
:class:`distutils2._backport.pkgutil.EggInfoDistribution` instances. The graph
is represented by the :class:`distutils2.depgraph.DependencyGraph` class that
keeps internally an adjacency list. Several functions are provided that
generate a graph in different manners. First, all of them are documented and
then several use case examples are provided along with graphviz illustrations
of the generated graphs.

API
---

.. automodule:: distutils2.depgraph
   :members:

Example Usage
-------------

