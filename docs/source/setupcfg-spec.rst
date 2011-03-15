===================
setup.cfg file v0.9
===================

This document describes the :file:`setup.cfg`, a ini-like file used by
Distutils2 to replace the :file:`setup.py` file.

Syntax
======

The configuration file is an ini-based file. Variables name can be
assigned values, and grouped into sections. A line that starts with "#" is
commented out. Empty lines are also removed.

Example::

    [section1] 
    # comment 
    name = value 
    name2 = "other value" 

    [section2] 
    foo = bar


Values conversion
:::::::::::::::::

Here are a set of rules for converting values:

- If value is quoted with " chars, it's a string. This notation is useful to
  include "=" characters in the value. In case the value contains a " 
  character, it must be escaped with a "\" character.
- If the value is "true" or "false" --no matter what the case is--, it's 
  converted to a boolean, or 0 and 1 when the language does not have a 
  boolean type.
- A value can contains multiple lines. When read, lines are converted into a
  sequence of values. Each new line for a multiple lines value must start with 
  a least one space or tab character. These indentation characters will be 
  stripped.
- all other values are considered as strings

Examples::

    [section]
    foo = one
          two
          three

    bar = false
    baz = 1.3
    boo = "ok"
    beee = "wqdqw pojpj w\"ddq"

Extending files
:::::::::::::::

An INI file can extend another file. For this, a "DEFAULT" section must contain
an "extends" variable that can point to one or several INI files which will be
merged to the current file by adding new sections and values.

If the file pointed in "extends" contains section/variable names that already
exist in the original file, they will not override existing ones.

file_one.ini::

    [section1]
    name2 = "other value"

    [section2]
    foo = baz
    bas = bar

file_two.ini::

    [DEFAULT]
    extends = file_one.ini

    [section2]
    foo = bar

Result::

    [section1]
    name2 = "other value"

    [section2]
    foo = bar
    bas = bar

To point several files, the multi-line notation can be used:

    [DEFAULT]
    extends = file_one.ini
            file_two.ini

When several files are provided, they are processed sequentially. So if the
first one has a value that is also present in the second, the second one will
be ignored. This means that the configuration goes from the most specialized to
the most common.

**Tools will need to provide a way to produce a canonical version of the 
file**. This will be useful to publish a single file.


Description of sections and fields
==================================

Each section contains a description of its options.

- Options that are marked *\*multi* can have multiple values, one value per
  line.
- Options that are marked *\*optional* can be omited.


The sections are:

global
    Global options for Distutils2.

metadata
    The metadata section contains the metadata for the project as described in
    :PEP:`345`.

files
    Declaration of package files included in the project.

`command` sections
    Redefinition of user options for Distutils2 commands.


global
::::::

Contains global options for Distutils2. This section is shared with Distutils1
(legacy version distributed in python 2.X standard library).


- **commands**: Defined Distutils2 command. A command is defined by its fully
  qualified name.

  Examples::

    [global]
    commands =
        package.sdist.CustomSdistCommand

  *\*optional* *\*multi*

- **compilers**: Defined Distutils2 compiler. A compiler is defined by its fully
  qualified name.

  Example::

    [global]
    compiler =
        package.compiler.CustomCCompiler

  *\*optional* *\*multi*

- **setup_hook**: defines a callable that will be called right after the
  :file:`setup.cfg` file is read. The callable receives the configuration
  in form of a mapping and can make some changes to it. *\*optional*

  Example::

    [global]
    setup_hook =
        distutils2.tests.test_config.hook


metadata
::::::::

The metadata section contains the metadata for the project as described in
:PEP:`345`. Field names are case-insensitive.

- metadata-version
- name
- version
- platform
- supported-platform
- summary
- description
- keywords
- home-page
- download-url
- author
- author-email
- maintainer
- maintainer-email
- license
- classifiers
- requires-dist
- provides-dist
- obsoletes-dist
- requires-python
- requires-externals
- project-url

There's one extra field, to replace description with a path to a text file:

- description-file: path to a text file that will be used to replace description


files
:::::

This section describes the files included in the project.

- **packages_root**: the root directory containing all packages. If not provided
  Distutils2 will use the current directory.  *\*optional*
- **packages**: a list of packages the project includes *\*optional* *\*multi*
- **modules**: a list of packages the project includes *\*optional* *\*multi*
- **scripts**: a list of scripts the project includes *\*optional* *\*multi*
- **extra_files**: a list of patterns to include extra files *\*optional* *\*multi*
- **resources**: a list of data files. *\*optional* *\*multi*

Example::

    [files]
    packages_root = src
    packages =
            pypi2rpm
            pypi2rpm.command

    scripts =
            pypi2rpm/pypi2rpm.py

    extra_files =
            setup.py
            README

    resources =
        source1 = destination1
        source2 = destination2
        doc/* = {doc}
        scripts/foo.sh = {datadir}/scripts/{distribution.name}

extensions
::::::::::


XXX

Command sections
:::::::::::::::::

Each Distutils2 command can have its own user options defined in :file:`setup.cfg`

Example::

    [sdist]
    manifest-builders = package.module.Maker


To override the build class in order to generate Python3 code from your Python2 base::

    [build_py]
    use-2to3 = True

Extensibility
=============

Every section can define new variable that are not part of the specification.
They are called **extensions**.

An extension field starts with *X-*.

Example::

    [metadata]
    ...
    X-Debian-Name = python-distribute

Changes in the specification
============================

The version scheme for this specification is **MAJOR.MINOR**.
Changes in the specification will increment the version.

- minor version changes (1.x): backwards compatible
 - new fields and sections (both optional and mandatory) can be added
 - optional fields can be removed 
- major channges (2.X): backwards-incompatible
 - mandatory fields/sections are removed
 - fields change their meaning

As a consequence, a tool written to consume 1.X (say, X=5) has these
properties:

- reading 1.Y, Y<X (e.g. 1.1) is possible, since the tool knows what 
  optional fields weren't there
- reading 1.Y, Y>X is also possible. The tool will just ignore the new 
  fields (even if they are mandatory in that version)
  If optional fields were removed, the tool will just consider them absent.
- reading 2.X is not possible; the tool should refuse to interpret
  the file.

A tool written to produce 1.X should have these properties:
- it will write all mandatory fields
- it may write optional fields

Acks
====

XXX

