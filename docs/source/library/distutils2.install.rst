==================
Installation tools
==================

In addition to the install commands, distutils2 provides a set of tools to deal
with installation of distributions.

Basically, they're intended to download the distribution from indexes, to
resolve the dependencies, and to provide a safe way to install all the
distributions.

You can find those tools in :module distutils2.install_tools:.


API
---

.. automodule:: distutils2.install
   :members:

Example usage
--------------

Get the scheme of what's gonna be installed if we install "foobar":

