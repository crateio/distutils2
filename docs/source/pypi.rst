=========================================
Tools to query PyPI: the PyPI package
=========================================

Distutils2 comes with a module (eg. `distutils2.pypi`) which contains
facilities to access the Python Package Index (named "pypi", and avalaible on
the url `http://pypi.python.org`.

There is two ways to retrieve data from pypi: using the *simple* API, and using
*XML-RPC*. The first one is in fact a set of HTML pages avalaible at
`http://pypi.python.org/simple/`, and the second one contains a set of XML-RPC
methods. In order to reduce the overload caused by running distant methods on 
the pypi server (by using the XML-RPC methods), the best way to retrieve 
informations is by using the simple API, when it contains the information you 
need.

Distutils2 provides two python modules to ease the work with those two APIs:
`distutils2.pypi.simple` and `distutils2.pypi.xmlrpc`. Both of them depends on 
another python module: `distutils2.pypi.dist`.


Requesting information via the "simple" API `distutils2.pypi.simple`
====================================================================

`distutils2.pypi.simple` can process the Python Package Index and return and 
download urls of distributions, for specific versions or latests, but it also 
can process external html pages, with the goal to find *pypi unhosted* versions 
of python distributions.

You should use `distutils2.pypi.simple` for: 

    * Search distributions by name and versions.
    * Process pypi external pages.
    * Download distributions by name and versions.

And should not be used to:

    * Things that will end up in too long index processing (like "finding all
      distributions with a specific version, no matters the name")

API
----

Here is a complete overview of the APIs of the SimpleIndex class.

.. autoclass:: distutils2.pypi.simple.SimpleIndex
    :members:

Usage Exemples
---------------

To help you understand how using the `SimpleIndex` class, here are some basic
usages.

Request PyPI to get a specific distribution
++++++++++++++++++++++++++++++++++++++++++++

Supposing you want to scan the PyPI index to get a list of distributions for 
the "foobar" project. You can use the "find" method for that::

    >>> from distutils2.pypi import SimpleIndex
    >>> client = SimpleIndex()
    >>> client.find("foobar")
    [<PyPIDistribution "Foobar 1.1">, <PyPIDistribution "Foobar 1.2">]
    
Note that you also can request the client about specific versions, using version
specifiers (described in `PEP 345 
<http://www.python.org/dev/peps/pep-0345/#version-specifiers>`_)::

    >>> client.find("foobar < 1.2")
    [<PyPIDistribution "foobar 1.1">, ]

`find` returns a list of distributions, but you also can get the last
distribution (the more up to date) that fullfil your requirements, like this::
    
    >>> client.get("foobar < 1.2")
    <PyPIDistribution "foobar 1.1">

Download distributions
+++++++++++++++++++++++

As it can get the urls of distributions provided by PyPI, the `SimpleIndex` 
client also can download the distributions and put it for you in a temporary
destination::

    >>> client.download("foobar")
    /tmp/temp_dir/foobar-1.2.tar.gz

You also can specify the directory you want to download to::
    
    >>> client.download("foobar", "/path/to/my/dir")
    /path/to/my/dir/foobar-1.2.tar.gz

While downloading, the md5 of the archive will be checked, if not matches, it
will try another time, then if fails again, raise `MD5HashDoesNotMatchError`.

Internally, that's not the SimpleIndex which download the distributions, but the
`PyPIDistribution` class. Please refer to this documentation for more details.

Following PyPI external links
++++++++++++++++++++++++++++++

The default behavior for distutils2 is to *not* follow the links provided
by HTML pages in the "simple index", to find distributions related
downloads.

It's possible to tell the PyPIClient to follow external links by setting the 
`follow_externals` attribute, on instanciation or after::

    >>> client = SimpleIndex(follow_externals=True)

or ::

    >>> client = SimpleIndex()
    >>> client.follow_externals = True

Working with external indexes, and mirrors
+++++++++++++++++++++++++++++++++++++++++++

The default `SimpleIndex` behavior is to rely on the Python Package index stored
on PyPI (http://pypi.python.org/simple).

As you can need to work with a local index, or private indexes, you can specify
it using the index_url parameter::

    >>> client = SimpleIndex(index_url="file://filesystem/path/")

or ::

    >>> client = SimpleIndex(index_url="http://some.specific.url/")

You also can specify mirrors to fallback on in case the first index_url you
provided doesnt respond, or not correctly. The default behavior for
`SimpleIndex` is to use the list provided by Python.org DNS records, as
described in the :pep:`381` about mirroring infrastructure.

If you don't want to rely on these, you could specify the list of mirrors you
want to try by specifying the `mirrors` attribute. It's a simple iterable::

    >>> mirrors = ["http://first.mirror","http://second.mirror"]
    >>> client = SimpleIndex(mirrors=mirrors)


Requesting informations via XML-RPC (`distutils2.pypi.XmlRpcIndex`)
==========================================================================

The other method to request the Python package index, is using the XML-RPC
methods. Distutils2 provides a simple wrapper around `xmlrpclib
<http://docs.python.org/library/xmlrpclib.html>`_, that can return you
`PyPIDistribution` objects.

::
    >>> from distutils2.pypi import XmlRpcIndex()
    >>> client = XmlRpcIndex()


PyPI Distributions
==================

Both `SimpleIndex` and `XmlRpcIndex` classes works with the classes provided
in the `pypi.dist` package.

`PyPIDistribution`
------------------

`PyPIDistribution` is a simple class that defines the following attributes:

:name:
    The name of the package. `foobar` in our exemples here
:version:
    The version of the package
:location:
    If the files from the archive has been downloaded, here is the path where
    you can find them.
:url:
    The url of the distribution

.. autoclass:: distutils2.pypi.dist.PyPIDistribution
    :members:

`PyPIDistributions`
-------------------

The `dist` module also provides another class, to work with lists of 
`PyPIDistribution` classes. It allow to filter results and is used as a 
container of 

.. autoclass:: distutils2.pypi.dist.PyPIDistributions
    :members:

At a higher level
=================

XXX : A description about a wraper around PyPI simple and XmlRpc Indexes
(PyPIIndex ?) 
