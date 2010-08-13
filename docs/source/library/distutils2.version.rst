======================
Working with versions
======================

Distutils2 ships with a python package capable to work with version numbers.
It's an implementation of version specifiers `as defined in PEP 345
<http://www.python.org/dev/peps/pep-0345/#version-specifiers>`_ about
Metadatas.

NormalizedVersion 
==================

A Normalized version is a specific version of a distribution, as
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

NormalizedVersion is used internally by `VersionPredicate` to do his stuff.

Suggest a normalized version
----------------------------

Before this version scheme, there was existing others ones. Distutils2 provides
a tool that suggests a normalized version: the `suggest_normalized_version` 
function::

    >>> suggest_normalized_version('2.1-rc1') 
    2.1c1

If `suggest_normalized_version` can't actually suggest you a version, it will
return `None`::

    >>> print suggest_normalized_version('not a version')
    None

Dealing with version predicates 
===============================

`VersionPredicate` knows how to parse stuff like "ProjectName (>=version)", the
class also provides a `match` method to test if a version number is the version
predicate::

    >>> version = VersionPredicate("ProjectName (<1.2,>1.0")
    >>> version.match("1.2.1")
    False
    >>> version.match("1.1.1")
    True

You could test if a predicate is a valid one, usng the `is_valid_predicate`
function::

    >>> is_valid_predicate('FooBar (1.1)')
    True
    >>> is_valid_predicate('FooBar (+1.1)')
    False

