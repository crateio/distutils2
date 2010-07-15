===================================
Query Python Package Indexes (PyPI)
===================================

Distutils2 provides facilities to access python package informations stored in
indexes. The main Python Package Index is available at http://pypi.python.org.

.. note:: The tools provided in distutils2 are not limited to query pypi, and
   can be used for others indexes, if they respect the same interfaces.

There is two ways to retrieve data from these indexes: using the *simple* API,
and using *XML-RPC*. The first one is a set of HTML pages avalaibles at
`http://pypi.python.org/simple/`, and the second one contains a set of XML-RPC
methods.

If you dont care about which API to use, the best thing to do is to let
distutils2 decide this for you, by using :class:`distutils2.index.Client`.

Of course, you can rely too on :class:`distutils2.index.simple.Crawler` and
:class:`distutils.index.xmlrpc.Client` if you need to use these specific APIs.

.. toctree::
    :maxdepth: 2

    projects-index.client.rst
    projects-index.dist.rst
    projects-index.simple.rst
    projects-index.xmlrpc.rst
