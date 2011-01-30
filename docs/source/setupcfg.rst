==================
The setup.cfg file
==================

This document describes the :file:`setup.cfg`, a ini-like file used by
Distutils2 to replace the :file:`setup.py` file.

Each section contains a description of its options.

- Options that are marked *\*multi* can have multiple values, one value
  per line.
- Options that are marked *\*optional* can be omited.
- Options that are marked *\*environ* can use environment markers, as described
  in :PEP:`345`.


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
======

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
    setup_hook = distutils2.tests.test_config.hook


metadata
========

The metadata section contains the metadata for the project as described in
:PEP:`345`.

.. Note::
    Field names are case-insensitive.

Fields:

- **name**: Name of the project.
- **version**: Version of the project. Must comply with :PEP:`386`.
- **platform**: Platform specification describing an operating system supported
  by the distribution which is not listed in the "Operating System" Trove
  classifiers (:PEP:`301`). *\*multi* *\*optional*
- **supported-platform**: Binary distributions containing a PKG-INFO file will
  use the Supported-Platform field in their metadata to specify the OS and
  CPU for which the binary distribution was compiled.  The semantics of
  the Supported-Platform field are freeform. *\*multi* *\*optional*
- **summary**: A one-line summary of what the distribution does.
  (Used to be called *description* in Distutils1.)
- **description**: A longer description. (Used to be called *long_description*
  in Distutils1.) A file can be provided in the *description-file* field.
  *\*optional*
- **description-file**: path to a text file that will be used for the
  **description** field. *\*optional*
- **keywords**: A list of additional keywords to be used to assist searching
  for the distribution in a larger catalog. Comma or space-separated. *\*optional*
- **home-page**: The URL for the distribution's home page.
- **download-url**: The URL from which this version of the distribution
  can be downloaded. *\*optional*
- **author**: Author's name. *\*optional*
- **author-email**: Author's e-mail. *\*optional*
- **maintainer**: Maintainer's name. *\*optional*
- **maintainer-email**: Maintainer's e-mail. *\*optional*
- **license**: A text indicating the term of uses, when a trove classifier does
  not match. *\*optional*.
- **classifiers**: Classification for the distribution, as described in PEP 301.
  *\*optional* *\*multi* *\*environ*
- **requires-dist**: name of another distutils project required as a dependency.
  The format is *name (version)* where version is an optional
  version declaration, as described in PEP 345. *\*optional* *\*multi* *\*environ*
- **provides-dist**: name of another distutils project contained whithin this
  distribution. Same format than *requires-dist*. *\*optional* *\*multi* *\*environ*
- **obsoletes-dist**: name of another distutils project this version obsoletes.
  Same format than *requires-dist*. *\*optional* *\*multi* *\*environ*
- **requires-python**: Specifies the Python version the distribution requires.
  The value is a version number, as described in PEP 345.
  *\*optional* *\*multi* *\*environ*
- **requires-externals**: a dependency in the system. This field is free-form,
  and just a hint for downstream maintainers. *\*optional* *\*multi* *\*environ*
- **project-url**: A label, followed by a browsable URL for the project.
  "label, url". The label is limited to 32 signs. *\*optional* *\*multi*


Example::

    [metadata]
    name = pypi2rpm
    version = 0.1
    author = Tarek Ziade
    author-email = tarek@ziade.org
    summary = Script that transforms a sdist archive into a rpm archive
    description-file = README
    home-page = http://bitbucket.org/tarek/pypi2rpm
    project-url: RSS feed, https://bitbucket.org/tarek/pypi2rpm/rss

    classifier = Development Status :: 3 - Alpha
        License :: OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)

.. Note::
    Some metadata fields seen in :PEP:`345` are automatically generated
    as the Metadata-Version value for instance.


files
=====

This section describes the files included in the project.

- **packages_root**: the root directory containing all packages. If not provided
  Distutils2 will use the current directory.  *\*optional*
- **packages**: a list of packages the project includes *\*optional* *\*multi*
- **modules**: a list of packages the project includes *\*optional* *\*multi*
- **scripts**: a list of scripts the project includes *\*optional* *\*multi*
- **extra_files**: a list of patterns to include extra files *\*optional* *\*multi*

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


`command` sections
==================

Each Distutils2 command can have its own user options defined in :file:`setup.cfg`

Example::

    [sdist]
    manifest-builders = package.module.Maker


To override the building class in order to compile your python2 files to python3::

    [build_py]
    use-2to3 = True


