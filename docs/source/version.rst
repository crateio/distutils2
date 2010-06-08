======================
Working with versions
======================

Distutils2 ships with a python package capable to work with version numbers.
It's an implementation of version specifiers `as defined in PEP 345
<http://www.python.org/dev/peps/pep-0345/#version-specifiers>`_ about
Metadata.

`distutils2.version.NormalizedVersion`
======================================

A Normalized version corresponds to a specific version of a distribution, as
described in the PEP 345. So, you can work with the `NormalizedVersion` like
this::

    >>> NormalizedVersion("1.2b1")
    NormalizedVersion('1.2b1')

If you try to use irrational version specifiers, an `IrrationalVersionError`
will be raised::

    >>> NormalizedVersion("irrational_version_number")
    ...
    IrrationalVersionError: irrational_version_number

You can compare NormalizedVersion objects, like this::

    >>> NormalizedVersion("1.2b1") < NormalizedVersion("1.2")
    True

NormalizedVersion is used internally by `Version`, `Versions` and
`VersionPredicate` to do their stuff.

`distutils2.version.suggest_normalized_version`
-----------------------------------------------

You also can let the normalized version be suggested to you, using the
`suggest_normalized_version` function::

    >>> suggest_normalized_version('2.1-rc1') 
    2.1c1

If `suggest_normalized_version` can't actually suggest you a version, it will
return `None`::

    >>> print suggest_normalized_version('not a version')
    None

`distutils2.version.VersionPredicate`
=====================================

`VersionPredicate` knows how to parse stuff like "ProjectName (>=version)", the
class also provides a `match` method to test if a version number is the version
predicate::

    >>> version = VersionPredicate("ProjectName (<1.2,>1.0")
    >>> version.match("1.2.1")
    False
    >>> version.match("1.1.1")
    True

`is_valid_predicate`
--------------------


`distutils2.version.Versions`
=============================

`is_valid_versions`
--------------------


`distutils2.version.Version`
============================

You can use the `Version` class to use version predicates without specifying a
project name. It works like `Versions`, but only for one version. See an
exemple::

    >>> Version("1.1")
    <distutils2.version.Version object at 0x...>

`is_valid_version`
--------------------
