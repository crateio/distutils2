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

Resources
=========

This section describes the files used by the project which must not be installed in the same place that python modules or libraries, they are called **resources**. They are for example documentation files, script files, databases, etc...

For declaring resources, you must use this notation ::

    source = destination

Data-files are declared in the **resources** field in the **file** section, for example::

    [files]
    resources =
        source1 = destination1
        source2 = destination2

The **source** part of the declaration are relative paths of resources files (using unix path separator **/**). For example, if you've this source tree::

    foo/
        doc/
            doc.man
        scripts/
            foo.sh
            
Your setup.cfg will look like::

    [files]
    resources =
        doc/doc.man = destination_doc
        scripts/foo.sh = destination_scripts
        
The final paths where files will be placed are composed by : **source** + **destination**. In the previous example, **doc/doc.man** will be placed in **destination_doc/doc/doc.man** and **scripts/foo.sh** will be placed in **destination_scripts/scripts/foo.sh**. (If you want more control on the final path, take a look at base_prefix_).

The **destination** part of resources declaration are paths with categories. Indeed, it's generally a bad idea to give absolute path as it will be cross incompatible. So, you must use resources categories in your **destination** declaration. Categories will be replaced by their real path at the installation time. Using categories is all benefit, your declaration will be simpler, cross platform and it will allow packager to place resources files where they want without breaking your code.

Categories can be specified by using this syntax::

    {category}
    
Default categories are::

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

A special category also exists **{distribution.name}** that will be replaced by the name of the distribution, but as most of the defaults categories use them, so it's not necessary to add **{distribution.name}** into your destination.

If you use categories in your declarations, and you are encouraged to do, final path will be::

    source + destination_expanded

.. _example_final_path:

For example, if you have this setup.cfg::

    [metadata]
    name = foo

    [files]
    resources =
        doc/doc.man = {doc}

And if **{doc}** is replaced by **{datadir}/doc/{distribution.name}**, final path will be::

    {datadir}/doc/foo/doc/doc.man
    
Where {datafir} category will be platform-dependent.

    
More control on source part
---------------------------

Glob syntax
___________

When you declare source file, you can use a glob-like syntax to match multiples file, for example::

    scripts/* = {script}
    
Will match all the files in the scripts directory and placed them in the script category.

Glob tokens are:

 * * : match all files.
 * ? : match any character.
 * ** : match any level of tree recursion (even 0).
 * {} : will match any part separated by comma (example : {sh,bat}).
 
TODO ::

    Add an example
    
Order of declaration
____________________

The order of declaration is important if one file match multiple rules. The last rules matched by file is used, this is useful if you have this source tree::

    foo/
        doc/
            index.rst
            setup.rst
            documentation.txt
            doc.tex
            README
            
And you want all the files in the doc directory to be placed in {doc} category, but README must be placed in {help} category, instead of listing all the files one by one, you can declare them in this way::

    [files]
    resources =
        doc/* = {doc}
        doc/README = {help}
        
Exclude
_______

You can exclude some files of resources declaration by giving no destination, it can be useful if you have a non-resources file in the same directory of resources files::

    foo/
        doc/
           RELEASES
           doc.tex
           documentation.txt
           docu.rst
           
Your **file** section will be::

    [files]
    resources =
        doc/* = {doc}
        doc/RELEASES =
        
More control on destination part
--------------------------------  

.. _base_prefix:

Define a base-prefix
____________________

When you define your resources, you can have more control of how the final path is compute.

By default, the final path is::

    destination + source
    
This can generate long paths, for example (example_final_path_)::

    {datadir}/doc/foo/doc/doc.man
    
When you declare your source, you can use a separator to split the source in **prefix** **suffix**. The supported separator are :

 * Whitespace
 
So, for example, if you have this source::

    docs/ doc.man
    
The **prefix** is "docs/" and the **suffix** is "doc.html".

.. note::

    Separator can be placed after a path separator or replace it. So theses two sources are equivalent::
    
        docs/ doc.man
        docs doc.man

.. note::

    Glob syntax is working the same way with standard source and splitted source. So theses rules::
    
        docs/*
        docs/ *
        docs *
        
    Will match all the files in the docs directory.
    
When you use splitted source, the final path is compute in this way::

    destination + prefix
    
So for example, if you have this setup.cfg::

    [metadata]
    name = foo

    [files]
    resources =
        doc/ doc.man = {doc}

And if **{doc}** is replaced by **{datadir}/doc/{distribution.name}**, final path will be::

    {datadir}/doc/foo/doc.man
    
    
Overwrite paths for categories
------------------------------

.. warning::

    This part is intended for system administrator or packager.
    
The real paths of categories are registered in the *sysconfig.cfg* file installed in your python installation. The format of this file is INI-like. The content of the file is  organized into several sections :

 * globals : Standard categories's paths.
 * posix_prefix : Standard paths for categories and installation paths for posix system.
 * other one...
 
Standard categories's paths are platform independent, they generally refers to other categories, which are platform dependent. Sysconfig module will choose these category from sections matching os.name. For example::

    doc = {datadir}/doc/{distribution.name}

It refers to datadir category, which can be different between platforms. In posix system, it may be::

    datadir = /usr/share
    
So the final path will be::

    doc = /usr/share/doc/{distribution.name}
    
The platform dependent categories are :
 
 * confdir
 * datadir
 * libdir
 * base

Define extra-categories
-----------------------

Examples
--------

.. note::

    These examples are incremental but works unitarily.

Resources in root dir
_____________________

Source tree::

  babar-1.0/
    README
    babar.sh
    launch.sh
    babar.py
    
Setup.cfg::

    [files]
    resources =
        README = {doc}
        *.sh = {scripts}
  
So babar.sh and launch.sh will be placed in {scripts} directory.

Now let's move all the scripts into a scripts directory.

Resources in sub-directory
__________________________

Source tree::

  babar-1.1/
    README
    scripts/
      babar.sh
      launch.sh
      LAUNCH
    babar.py
    
Setup.cfg::

    [files]
    resources =
        README = {doc}
        scripts/ LAUNCH = {doc}
        scripts/ *.sh = {scripts}
  
It's important to use the separator after scripts/ to install all the bash scripts into {scripts} instead of {scripts}/scripts.

Now let's add some docs.

Resources in multiple sub-directories
_____________________________________

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

   [files]
   resources =
        README = {doc}
        scripts/ LAUNCH = {doc}
        scripts/ *.sh = {scripts}
        doc/ * = {doc}
        doc/ man = {man}
  
You want to place all the file in the docs script into {doc} category, instead of man, which must be placed into {man} category, we will use the order of declaration of globs to choose the destination, the last glob that match the file is used.

Now let's add some scripts for windows users.
  
Complete example
________________

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

    [files]
    resources = 
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


