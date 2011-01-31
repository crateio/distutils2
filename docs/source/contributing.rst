==========================
Contributing to Distutils2
==========================

----------------
Reporting Issues
----------------

When using, testing, developping distutils2, you may encounter issues. Please report to the following sections to know how these issues should be reported.

Please keep in mind that this guide is intended to ease the triage and fixing processes by giving the maximum information to the developers. It should not be viewed as mandatory, only advised ;).

Issues regarding distutils2 commands
====================================

- Go to http://bugs.python.org/ (you'll need a Python Bugs account), then "Issues" > "Create ticket".
- **Title**: write in a short summary of the issue. 
    * You may prefix the issue title with [d2_component], where d2_component can be : installer, sdist, setup.cfg, ... This will ease up the triage process.

- **Components**: choose "Distutils2"
- **Version**: choose "3rd party"
- **Comment**: use the following template for versions, reproduction conditions:
    * If some of the fields presented don't apply to the issue, feel free to pick only the ones you need.

::

    Operating System:
    Version of Python:
    Version of Distutils2:

    How to reproduce:

    What happens:

    What should happen:

- Filling in the fields:
    * **How to reproduce**: indicate some test case to reproduce the issue.
    * **What happens**: describe what is the error, paste tracebacks if you have any.
    * **What should happen**: indicate what you think should be the result of the test case (wanted behaviour).
    * **Versions**:
        - If you're using a release of distutils2, you may want to test the latest version of the project (under developpment code).
        - If the issue is present in the latest version, please indicate the tip commit of the version tested.
        - Be careful to indicate the remote reference (12 characters, for instance c3cf81fc64db), not the local reference (rXXX).

- If it is relevant, please join any file that will help reproducing the issue or logs to understand the problem (setup.cfg, strace ouptups, ...).

Issues regarding PyPI display of the distutils2 projects
========================================================

- Please send a bug report to the catalog-sig@python.org mailing list.
- You can include your setup.cfg, and a link to your project page.
