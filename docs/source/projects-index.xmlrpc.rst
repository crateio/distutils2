=========================
Query indexes via XML-RPC
=========================

Indexes can be queried using XML-RPC calls, and Distutils2 provides a simple
way to interface with XML-RPC.

You should **use** XML-RPC when:

    * Searching the index for projects **on other fields than project 
      names**. For instance, you can search for projects based on the 
      author_email field. 
    * Searching all the versions that have existed for a project.
    * you want to retrive METADATAs informations from releases or
      distributions.

You should **avoid using** XML-RPC method calls when:

    * Retrieving the last version of a project
    * Getting the projects with a specific name and version.
    * The simple index can match your needs

When dealing with indexes, keep in mind that the index queriers will always
return you :class:`distutils2.index.ReleaseInfo` and 
:class:`distutils2.index.ReleasesList` objects.

Some methods here share common APIs with the one you can find on
:class:`distutils2.index.simple`, internally, :class:`distutils2.index.client`
is inherited by :class:`distutils2.index.xmlrpc.Client`

API
====

.. autoclass:: distutils2.index.xmlrpc.Client
    :members:

Usage examples
===============

Use case described here are use case that are not common to the other clients.
If you want to see all the methods, please refer to API or to usage examples
described in :class:`distutils2.index.client.Client`

Finding releases
----------------

It's a common use case to search for "things" within the index.
We can basically search for projects by their name, which is the 
most used way for users (eg. "give me the last version of the FooBar project").
This can be accomplished using the following syntax::

    >>> client = xmlrpc.Client()
    >>> client.get_release("Foobar (<= 1.3))
    <FooBar 1.2.1>
    >>> client.get_releases("FooBar (<= 1.3)")
    [FooBar 1.1, FooBar 1.1.1, FooBar 1.2, FooBar 1.2.1]

And we also can find for specific fields::

    >>> client.search_projects(field=value)

You could specify the operator to use, default is "or"::

    >>> client.search_projects(field=value, operator="and")

The specific fields you can search are:

    * name
    * version
    * author
    * author_email
    * maintainer
    * maintainer_email
    * home_page
    * license
    * summary
    * description
    * keywords
    * platform
    * download_url 

Getting metadata informations
-----------------------------

XML-RPC is a prefered way to retrieve metadata informations from indexes.
It's really simple to do so::

    >>> client = xmlrpc.Client()
    >>> client.get_metadata("FooBar", "1.1")
    <ReleaseInfo FooBar 1.1>

Assuming we already have a :class:`distutils2.index.ReleaseInfo` object defined,
it's possible to pass it ot the xmlrpc client to retrieve and complete it's
metadata::

    >>> foobar11 = ReleaseInfo("FooBar", "1.1")
    >>> client = xmlrpc.Client()
    >>> returned_release = client.get_metadata(release=foobar11)
    >>> returned_release
    <ReleaseInfo FooBar 1.1>

Get all the releases of a project
---------------------------------

To retrieve all the releases for a project, you can build them using
`get_releases`::

    >>> client = xmlrpc.Client()
    >>> client.get_releases("FooBar")
    [<ReleaseInfo FooBar 0.9>, <ReleaseInfo FooBar 1.0>, <ReleaseInfo 1.1>]

Get informations about distributions
------------------------------------

Indexes have informations about projects, releases **and** distributions.
If you're not familiar with those, please refer to the documentation of
:mod:`distutils2.index.dist`.

It's possible to retrive informations about distributions, e.g "what are the
existing distributions for this release ? How to retrieve them ?"::

    >>> client = xmlrpc.Client()
    >>> release = client.get_distributions("FooBar", "1.1")
    >>> release.dists
    {'sdist': <FooBar 1.1 sdist>, 'bdist': <FooBar 1.1 bdist>}

As you see, this does not return a list of distributions, but a release, 
because a release can be used like a list of distributions. 
