===============================
High level API to Query indexes
===============================

Distutils2 provides a high level API to query indexes, search for releases and
distributions, no matters the underlying API you want to use.

The aim of this module is to choose the best way to query the API, using the
less possible XML-RPC, and when possible the simple index.

API
===

The client comes with the common methods "find_projects", "get_release" and
"get_releases", which helps to query the servers, and returns
:class:`distutils2.index.dist.ReleaseInfo`, and
:class:`distutils2.index.dist.ReleasesList` objects.

.. autoclass:: distutils2.index.wrapper.ClientWrapper
    :members:
