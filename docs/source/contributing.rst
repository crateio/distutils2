==========================
Contributing to Distutils2
==========================

----------------
Reporting Issues
----------------

When using, testing or developping distutils2, you may encounter issues. Please report to the following sections to know how these issues should be reported.

Please keep in mind that this guide is intended to ease the triage and fixing processes by giving the maximum information to the developers. It should not be viewed as mandatory, only advisory ;).


- Go to http://bugs.python.org/ (you'll need a Python Bugs account), then "Issues" > "Create ticket".
- **Title**: write in a short summary of the issue. You may prefix the issue title with “component:”, where component can be something like installer, sdist, setup.cfg, etc., or add it at the end of your title if the normal flow of the sentence allows it. This will ease up later searches.
- **Components**: choose "Distutils2"
- **Version**: choose "3rd party"
- **Body**: explain how to reproduce the bug: What you want to do, what code you write, what happens, what should happen, how to fix it (if you have an idea).
   * You should always test with the tip of the main repository, not releases.
   * Mention the versions of Python you tested with.  d2 supports 2.4 to 2.7.
   * If relevant, mention the version of your operating system (for example with issues related to C extensions).
   * When referencing commits, be careful to use the universal changeset identifiers (12 characters, for instance c3cf81fc64db), not the local sequential numbers (for example 925) that are not shared among clones.
   * Try to be as concise as possible, but not too much.
   * If useful, paste tracebacks.
   * If useful, attach setup.cfg or other files (binary files like archives are not very convenient, better to stick to text).

Issues related to PyPI are reported via email to the **catalog-sig@python.org** mailing list, not within bugs.python.org.
