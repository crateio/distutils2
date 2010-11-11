.. Distutils2 doc site master file
   This doc serves as project homepage and documentation preview
   (on distutils2.notmyidea.org) until distutils2 is merged back into
   the Python standard library.
   This file should contain the root `toctree` directive.


Welcome to Distutils2!
======================

Distutils2 is the new, improved version of the Python Distribution Utilities,
a library used to package, distribute, build and install Python projects.

- `Origin of the project`__
- `Main code repository`__
- `Clones of this repository`__
- `Bug tracker`__ (some bugs may be assigned only to Distutils)
- `Teams that worked on Distutils2 for Google Summer of Code 2010`__ (links to
  their code repositories and weblogs)

.. __: http://tarekziade.wordpress.com/2010/03/03/
       the-fate-of-distutils-pycon-summit-packaging-sprint-detailed-report/
.. __: http://bitbucket.org/tarek/distutils2/
.. __: http://bitbucket.org/tarek/distutils2/descendants/
.. __: http://bugs.python.org/issue?%40sort0=activity&%40sortdir0=on&%40sort1=
       &%40group0=priority&%40group1=&%40columns=title%2Cid%2Cactivity%2Cstatus
       &%40filter=components%2Cstatus&status=1&components=25&%40pagesize=50
       &%40startwith=0
.. __: http://bitbucket.org/tarek/distutils2/wiki/GSoC_2010_teams

If you’re looking for information on how to contribute, head to
:doc:`devresources`.


Documentation
-------------

These documents are the in-development version of Distutils2's documentation,
started from the existing Distutils documentation and updated by the
Distutils2 group (GSoC students, mentors, volunteers).

Please remember that this is a work in progress. The documentation is not
complete, not spell-checked, and uses different styles.

The documentation is split in four sections, as in the standard Python docs:

:doc:`install/index`
  A guide for for end-users wanting to install a Python application or
  library.

:doc:`setupcfg`
  Specifications of setup.cfg, the most important file for developers.

:doc:`tutorial`
  A tutorial for Python developers to discover Distutils2 main features.

:doc:`distutils/index`
  A guide for Python developers wanting to package and distribute their
  project.

:doc:`library/distutils2`
  A reference for developers wanting to use standalone building blocks like
  :mod:`~distutils2.version` or :mod:`~distutils2.metadata`, or extend
  Distutils2 itself. Since :PEP:`376` is partly implemented in the
  :mod:`pkgutil` module, its updated documentation is also included:
  :doc:`library/pkgutil`.


.. toctree::
   :hidden:

   devresources
   install/index
   setupcfg
   tutorial
   distutils/index
   library/distutils2
   library/pkgutil


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
