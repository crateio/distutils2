=================
The PyPI Module
=================

Distutils2 comes with a module (eg. `distutils2.pypi`) which contains
facilities to access the Python Package Index (named "pypi", and avalaible on
the url `http://pypi.python.org`.

There is two ways to retreive data from pypi: using the *simple* API, and using
*XML-RPC*. The first one is in fact a set of HTML pages avalaible at
`http://pypi.python.org/simple/`. In order to reduce the overload caused by
running distant methods on the pypi server (by using the XML-RPC methods), the
best way to retreive informations is by using the simple API.

Distutils2 provides two python modules to ease the work with those two APIs:
`distutils2.pypi.simple` and `distutils2.pypi.xmlrpc`.

`distutils2.pypi.dist`
======================

Both `SimpleIndex` and `XmlRpcIndex` classes works with `PyPIDistribution` 
classes.
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


Requesting information via the "simple" API `distutils2.pypi.simple`
====================================================================

`distutils2.pypi.simple` can process the Python Package Index and return and 
download urls of distributions, for specific versions or latests, but it also 
can process external html pages, with the goal to find *pypi unhosted* versions 
of python distributions.

You should use `distutils2.pypi.simple` way of accessing data should be used 
to:

    * Search distributions by name and versions.
    * Process pypi external pages.
    * Download distributions by name and versions.

And should not be used to:

    * Things that will end up in too long index processing (like "finding all
      distributions with a specific version, no matters the name")

Request PyPI to get a specific distribution
--------------------------------------------

Supposing you want to scan the PyPI index to get a list of distributions for 
the "foobar" project::

    >>> from distutils2.pypi import SimpleIndex
    >>> client = SimpleIndex()
    >>> client.get_distributions("foobar")
    [<PyPIDistribution "Foobar 1.1">, <PyPIDistribution "Foobar 1.2">]
    
Then, you can get all the distribution found by the `Simple` class using the
following syntax::

    >>> client["foobar"]
    [<PyPIDistribution "Foobar 1.1">, <PyPIDistribution "Foobar 1.2">]

Note that you also can request the client about specific versions, using version
specifiers (described in `PEP 345 
<http://www.python.org/dev/peps/pep-0345/#version-specifiers>`_)::

    >>> client.get_distributions("foobar < 1.2")
    [<PyPIDistribution "Foobar 1.1">, ]

Download distributions
----------------------

As it can get the urls of distributions provided by PyPI, the `Simple` client
also can download the distributions and put it for you in a temporary
destination::

    >>> client.download("foobar")
    /tmp/temp_dir/foobar-1.2.tar.gz

You also can specify the directory you want to download to::
    
    >>> client.download("foobar", "/path/to/my/dir")
    /path/to/my/dir/foobar-1.2.tar.gz

While downloading, the md5 of the archive will be checked, if not matches, it
will try another time, then if fails again, raise `InvalidMd5Error`.

XXX: Maybe try external urls if provided, if it fails ?

Requesting external pages
-------------------------

The default behavior for distutils2 is to follow the links provided
by distributions within their metadatas, and find distributions related
downloads.

When downloading, then, it will first use the packages found ont PyPI, then
falling back to external webpages if needed.

It's possible to tell the PyPIClient to not follow external links by specifying
the `follow_external` parameter to the constructor::

    >>> client = SimpleIndex(follow_externals=False)

Or later by changing it's value::

    >>> client.follow_externals = True


Requesting informations via XML-RPC (`distutils2.pypi.XmlRpcIndex`)
==========================================================================

The other method to request the Python package index, is using the XML-RPC
methods. Distutils2 provides a simple wrapper around `xmlrpclib
<http://docs.python.org/library/xmlrpclib.html>`_, that can return you
`PyPIDistribution` objects.

::
    >>> from distutils2.pypi import XmlRpcIndex()
    >>> client = XmlRpcIndex()


At a higher level
=================

XXX : A description about a wraper around PyPI simple and XmlRpc Indexes
(PyPiIndex ?) 
