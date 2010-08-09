===============================
Dependency Graph Builder Module
===============================

Introduction
------------

This module provides the means to analyse the dependencies between various
distributions and furthermore to create a graph representing the relationships
from a list of :class:`distutils2._backport.pkgutil.Distribution` and
:class:`distutils2._backport.pkgutil.EggInfoDistribution` instances. The graph
is represented by the :class:`distutils2.depgraph.DependencyGraph` class that
keeps internally an adjacency list. Several functions are provided that
generate a graph in different manners. First, all of them are documented and
then several use case examples are provided along with
`graphviz <http://www.graphviz.org/>`_ illustrations
of the generated graphs.

API
---

.. automodule:: distutils2.depgraph
   :members:

Example Usage
-------------

Depict all Dependenciess in the System
++++++++++++++++++++++++++++++++++++++

First, we shall generate a graph of all the distributions on the system
and then create an image out of it using the tools provided by
`graphviz <http://www.graphviz.org/>`_. For obtaining the list of
installed distributions, we will use the functions provided by the module
:mod:`distutils2._backport.pkgutil`::

  from distutils2._backport.pkgutil import get_distributions
  from distutils2.depgraph import generate_graph

  dists = list(pkgutil.get_distributions())
  graph = generate_graph(dists)

Now, it would be of interest to print out the missing requirements. This
can be done as follows::

  for dist, reqs in graph.missing.iteritems():
      if len(reqs) > 0:
          reqs_s = " ,".join(reqs)
          print("Missing dependencies for %s: %s" % (dist.name, reqs_s))

Example output on my configuration is:

.. code-block:: none

  Missing dependencies for TurboCheetah: Cheetah
  Missing dependencies for TurboGears: ConfigObj, DecoratorTools, RuleDispatch
  Missing dependencies for jockey: PyKDE4.kdecore, PyKDE4.kdeui, PyQt4.QtCore, PyQt4.QtGui
  Missing dependencies for TurboKid: kid
  Missing dependencies for TurboJson: DecoratorTools, RuleDispatch

Now, we proceed with generating a graphical representation of the graph. First
we write it to a file, and then we generate a PNG image using the ``dot``
command-line tool::

  from distutils2.depgraph import graph_to_dot
  f = open('output.dot', 'w')
  # we only show the interesting distributions, skipping the disconnected ones
  graph_to_dot(graph, f, skip_disconnected=True)

Now, we can create the actual picture using:

.. code-block:: bash

  $ dot -Tpng output.dot > output.png

An example output image is:

.. figure:: images/depgraph_output.png
   :alt: An example dot output

If you want to include ``.egg`` and ``.egg-info`` distributions as well, then
the code requires only one change, namely the line::

  dists = list(pkgutil.get_distributions())

has to be replaced with::

  dists = list(pkgutil.get_distributions(use_egg_info=True))

Then, on most platforms, a richer graph is obtained because at the moment most
distributions are provided in the ``.egg``/``.egg-info`` rather than the
``.dist-info`` format. An example of a more involved graph for illustrative
reasons can be seen `here <_static/depgraph_big.png>`_.


List all Dependent Distributions
++++++++++++++++++++++++++++++++

We will list all distributions that are dependent on some given distibution.
This time, ``.egg``/``.egg-info`` distributions will be considered as well::

  from distutils2._backport.pkgutil import get_distributions
  from distutils2.depgraph import dependent_dists
  import sys

  dists = list(get_distributions(use_egg_info=True))
  dist = None
  for d in dists:
      if d.name == 'bacon':
          dist = d
          break
  if dist is None:
     print('No such distribution in the system')
     sys.exit(1)
  deps = dependent_dists(dists, dist)
  deps_s = ", ".join([x.name for x in deps])
  print("The following distributions depend on %s: %s" % (dist.name, deps_s))

And this is example output with the dependency relationships as in the
`previous section <_static/depgraph_big.png>`_:

.. code-block:: none

  The following distributions depend on bacon: towel-stuff, choxie, grammar

