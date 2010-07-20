===============================
High level API to Query indexes
===============================

Distutils2 provides a high level API to query indexes, search for releases and
distributions, no matters the underlying API you want to use.

The aim of this module is to choose the best way to query the API, using the
less possible XML-RPC, and when possible the simple index. 

.. note:: This index is not yet available, so please rely on XMLRPC client or
   Simple Crawler to browse indexes.

API
===

The client comes with the common methods "find", "get" and "download", which
helps to query the servers, and returns.

:class:`distutils2.index.dist.ReleaseInfo`, and
:class:`distutils2.index.dist.ReleasesList` objects.

XXX TODO Autoclass here.

Exemples
=========

