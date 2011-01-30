==================
The setup.cfg file
==================

This document describes the :file:`setup.cfg`, a ini-like file used by
Distutils2 to replace the :file:`setup.py` file.

Each section contains a description of its options.

- Options that are marked *\*multi* can have multiple values, one value per
  line.
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
    setup_hook =
        distutils2.tests.test_config.hook


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
    (for instance Metadata-Version value).


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
            README

.. Note::
    In Distutils2, setup.cfg will be implicitly included.

data-files
==========


TODO :

        ###
        source -> destination
        
        final-path = destination + source
        
        There is an {alias} for each categories of datafiles
        -----
        source may be a glob (*, ?, **, {})
        
        order
        
        exclude
        --
        base-prefix
        
        ####
        overwrite system config for {alias}
        
        ####
        extra-categories

This section describes the files used by the project which must not be installed in the same place that python modules or libraries.

The format for specifing data files is :

 **source** = **destination**
 
Example::

    scripts/script1.bin = {scripts}
    
It means that the file scripts/script1.bin will be placed 

It means that every file which match the glob_syntax will be placed in the destination. A part of the path of the file will be stripped when it will be expanded and another part will be append to the destination. For more informations about which part of the path will be stripped or not, take a look at next sub-section globsyntax_.

The destination path will be expanded at the installation time using categories's default-path in the sysconfig.cfg file in the system. For more information about categories's default-paths, take a look at next next sub-section destination_.


.. _globsyntax:

glob_syntax
-----------

The glob syntax is traditionnal glob syntax (with unix separator **/**) with one more information : what part of the path will be stripped when path will be expanded ?

The special character which indicate the end of the part that will be stripped and the beginning of the part that will be added is whitespace, which can follow or replace a path separator.

Example::

    scripts/ *.bin
    
is equivalent to::

    scripts *.bin

Theses examples means that all files with extensions bin in the directory scripts will be placed directly on **destination** directory.

This glob example::

    scripts/*.bin
    
means that all files with extensions bin in the directory scripts will be placed directly on **destination/scripts** directory.

.. _destination:

destination
-----------

The destination is a traditionnal path (with unix separator **/**) where some parts will be expanded at installation time. These parts look like **{category}**, they will be expanded by reading system-wide default-path stored in sysconfig.cfg. Defaults categories are :

* config
* appdata
* appdata.arch
* appdata.persistent
* appdata.disposable
* help
* icon
* scripts
* doc
* info
* man

A special category exists, named {distribution.name} which will be expanded into your distribution name. You should not use it in your destination path, as they are may be used in defaults categories::

    [globals]
    # These are the useful categories that are sometimes referenced at runtime,
    # using pkgutil.open():
    # Configuration files
    config = {confdir}/{distribution.name}
    # Non-writable data that is independent of architecture (images, many xml/text files)
    appdata = {datadir}/{distribution.name}
    # Non-writable data that is architecture-dependent (some binary data formats)
    appdata.arch = {libdir}/{distribution.name}
    # Data, written by the package, that must be preserved (databases)
    appdata.persistent = {statedir}/lib/{distribution.name}
    # Data, written by the package, that can be safely discarded (cache)
    appdata.disposable = {statedir}/cache/{distribution.name}
    # Help or documentation files referenced at runtime
    help = {datadir}/{distribution.name}
    icon = {datadir}/pixmaps
    scripts = {base}/bin
    
    # Non-runtime files.  These are valid categories for marking files for
    # install, but they should not be referenced by the app at runtime:
    # Help or documentation files not referenced by the package at runtime
    doc = {datadir}/doc/{distribution.name}
    # GNU info documentation files
    info = {datadir}/info
    # man pages
    man = {datadir}/man

So, if you have this destination path : **{help}/api**, it will be expanded into **{datadir}/{distribution.name}/api**. {datadir} will be expanded depending on your system value (ex : confdir = datadir = /usr/share/).


Simple-example
--------------

Source tree::

  babar-1.0/
    README
    babar.sh
    launch.sh
    babar.py
    
Setup.cfg::

  [RESOURCES]
  README = {doc}
  *.sh = {scripts}
  
So babar.sh and launch.sh will be placed in {scripts} directory.

Now let's create to move all the scripts into a scripts/directory.

Second-example
--------------

Source tree::

  babar-1.1/
    README
    scripts/
      babar.sh
      launch.sh
      LAUNCH
    babar.py
    
Setup.cfg::

  [RESOURCES]
  README = {doc}
  scripts/ LAUNCH = {scripts}
  scripts/ *.sh = {scripts}
  
It's important to use the separator after scripts/ to install all the bash scripts into {scripts} instead of {scripts}/scripts.

Now let's add some docs.

Third-example
-------------

Source tree::

  babar-1.2/
    README
    scripts/
      babar.sh
      launch.sh
      LAUNCH
    docs/
      api
      man
    babar.py

Setup.cfg::

  [RESOURCES]
  README = {doc}
  scripts/ LAUNCH = {doc}
  scripts/ *.sh = {scripts}
  doc/ * = {doc}
  doc/ man = {man}
  
You want to place all the file in the docs script into {doc} category, instead of man, which must be placed into {man} category, we will use the order of declaration of globs to choose the destination, the last glob that match the file is used.

Now let's add some scripts for windows users.
  
Final example
-------------

Source tree::

  babar-1.3/
    README
    doc/
      api
      man
    scripts/  
      babar.sh
      launch.sh
      babar.bat
      launch.bat
      LAUNCH

Setup.cfg::

  [RESOURCES]
  README = {doc}
  scripts/ LAUNCH = {doc}
  scripts/ *.{sh,bat} = {scripts}
  doc/ * = {doc}
  doc/ man = {man}

We use brace expansion syntax to place all the bash and batch scripts into {scripts} category.

.. Warning::
    In Distutils2, setup.py and README (or README.txt) files are not more
    included in source distribution by default


`command` sections
==================

Each Distutils2 command can have its own user options defined in :file:`setup.cfg`

Example::

    [sdist]
    manifest-builders = package.module.Maker


To override the build class in order to generate Python3 code from your Python2 base::

    [build_py]
    use-2to3 = True


