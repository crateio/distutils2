===================================
Query Python Package Indexes (PyPI)
===================================

Distutils2 queries PyPI to get information about projects or download those
projects. The low-level facilities used internally are also part of the public
API destined to be used by other tools.

The :mod:`distutils2.index` package provides those facilities, which can be
used to access informations about Python projects registered at indexes, the
main one being PyPI, located ad http://pypi.python.org/.

There is two ways to retrieve data from these indexes: using the *simple* API,
and using *XML-RPC*. The first one is a set of HTML pages avalaibles at
`http://pypi.python.org/simple/`, and the second one contains a set of XML-RPC
methods. Mirrors typically implement the simple interface.

If you dont care about which API to use, the best thing to do is to let
distutils2 decide this for you, by using :class:`distutils2.index.ClientWrapper`.

Of course, you can rely too on :class:`distutils2.index.simple.Crawler` and
:class:`distutils2.index.xmlrpc.Client` if you need to use a specific API.

.. toctree::
    :maxdepth: 2
    :numbered:

    distutils2.index.client
    distutils2.index.dist
    distutils2.index.simple
    distutils2.index.xmlrpc
