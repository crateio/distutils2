==================================================
Representation of informations coming from indexes 
==================================================

Informations coming from indexes are represented by the classes present in the
`dist` module.

APIs
====

Keep in mind that each project (eg. FooBar) can have several releases 
(eg. 1.1, 1.2, 1.3), and each of these releases can be provided in multiple 
distributions (eg. a source distribution, a binary one, etc).

ReleaseInfo
------------

Each release have a project name, a project version and contain project
metadata. In addition, releases contain the distributions too. 

These informations are stored in :class:`distutils2.index.dist.ReleaseInfo` 
objects.

.. autoclass:: distutils2.index.dist.ReleaseInfo
    :members:

DistInfo
---------

:class:`distutils2.index.dist.DistInfo` is a simple class that contains
informations related to distributions. It's mainly about the URLs where those
distributions can be found. 

.. autoclass:: distutils2.index.dist.DistInfo
    :members:

ReleasesList
------------

The `dist` module also provides another class, to work with lists of 
:class:`distutils.index.dist.ReleaseInfo` classes. It allow to filter 
and order results.

.. autoclass:: distutils2.index.dist.ReleasesList
    :members:

Exemple usages
===============

Build a list of releases, and order them
----------------------------------------

Assuming we have a list of releases::

    >>> from distutils2.index.dist import ReleaseList, ReleaseInfo
    >>> fb10 = ReleaseInfo("FooBar", "1.0")
    >>> fb11 = ReleaseInfo("FooBar", "1.1")
    >>> fb11a = ReleaseInfo("FooBar", "1.1a1")
    >>> ReleasesList("FooBar", [fb11, fb11a, fb10])
    >>> releases.sort_releases()
    >>> releases.get_versions()
    ['1.1', '1.1a1', '1.0']
    >>> releases.add_release("1.2a1")
    >>> releases.get_versions()
    ['1.1', '1.1a1', '1.0', '1.2a1']
    >>> releases.sort_releases()
    ['1.2a1', '1.1', '1.1a1', '1.0']
    >>> releases.sort_releases(prefer_final=True)
    >>> releases.get_versions()
    ['1.1', '1.0', '1.2a1', '1.1a1']


Add distribution related informations to releases
-------------------------------------------------

It's easy to add distribution informatons to releases::

    >>> from distutils2.index.dist import ReleaseList, ReleaseInfo
    >>> r = ReleaseInfo("FooBar", "1.0")
    >>> r.add_distribution("sdist", url="http://example.org/foobar-1.0.tar.gz") 
    >>> r.dists
    {'sdist': FooBar 1.0 sdist}
    >>> r['sdist'].url
    {'url': 'http://example.org/foobar-1.0.tar.gz', 'hashname': None, 'hashval':
    None, 'is_external': True}
 
Attributes Lazy loading
-----------------------

To abstract a maximum the way of querying informations to the indexes,
attributes and releases informations can be retrieved "on demand", in a "lazy"
way.

For instance, if you have a release instance that does not contain the metadata
attribute, it can be build directly when accedded::

    >>> r = Release("FooBar", "1.1")
    >>> print r._metadata 
    None # metadata field is actually set to "None"
    >>> r.metadata
    <Metadata for FooBar 1.1>

Like this, it's possible to retrieve project's releases, releases metadata and 
releases distributions informations. 

Internally, this is possible because while retrieving for the first time
informations about projects, releases or distributions, a reference to the
client used is stored in the objects. Then, while trying to access undefined
fields, it will be used if necessary.
