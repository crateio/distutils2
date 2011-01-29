from tempfile import mkdtemp
import logging
import shutil
import os
import errno
import itertools

from distutils2._backport.pkgutil import get_distributions
from distutils2.depgraph import generate_graph
from distutils2.index import wrapper
from distutils2.index.errors import ProjectNotFound, ReleaseNotFound

"""Provides installations scripts.

The goal of this script is to install a release from the indexes (eg.
PyPI), including the dependencies of the releases if needed.

It uses the work made in pkgutil and by the index crawlers to browse the
installed distributions, and rely on the instalation commands to install.
"""


class InstallationException(Exception):
    """Base exception for installation scripts"""


class InstallationConflict(InstallationException):
    """Raised when a conflict is detected"""


def move_files(files, destination=None):
    """Move the list of files in the destination folder, keeping the same
    structure.

    Return a list of tuple (old, new) emplacement of files

    :param files: a list of files to move.
    :param destination: the destination directory to put on the files.
                        if not defined, create a new one, using mkdtemp
    """
    if not destination:
        destination = mkdtemp()

    for old in files:
        new = '%s%s' % (destination, old)

        # try to make the paths.
        try:
            os.makedirs(os.path.dirname(new))
        except OSError, e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise e
        os.rename(old, new)
        yield(old, new)


def install_dists(dists, path=None):
    """Install all distributions provided in dists, with the given prefix.

    If an error occurs while installing one of the distributions, uninstall all
    the installed distribution (in the context if this function).

    Return a list of installed files.

    :param dists: distributions to install
    :param path: base path to install distribution on
    """
    if not path:
        path = mkdtemp()

    installed_dists, installed_files = [], []
    for d in dists:
        try:
            installed_files.extend(d.install(path))
            installed_dists.append(d)
        except Exception, e :
            for d in installed_dists:
                d.uninstall()
            raise e
    return installed_files


def install_from_infos(install=[], remove=[], conflicts=[], install_path=None):
    """Install and remove the given distributions.

    The function signature is made to be compatible with the one of get_infos.
    The aim of this script is to povide a way to install/remove what's asked,
    and to rollback if needed.

    So, it's not possible to be in an inconsistant state, it could be either
    installed, either uninstalled, not half-installed.

    The process follow those steps:

        1. Move all distributions that will be removed in a temporary location
        2. Install all the distributions that will be installed in a temp. loc.
        3. If the installation fails, rollback (eg. move back) those
           distributions, or remove what have been installed.
        4. Else, move the distributions to the right locations, and remove for
           real the distributions thats need to be removed.

    :param install: list of distributions that will be installed.
    :param remove: list of distributions that will be removed.
    :param conflicts: list of conflicting distributions, eg. that will be in
                      conflict once the install and remove distribution will be
                      processed.
    :param install_path: the installation path where we want to install the
                         distributions.
    """
    # first of all, if we have conflicts, stop here.
    if conflicts:
        raise InstallationConflict(conflicts)

    # before removing the files, we will start by moving them away
    # then, if any error occurs, we could replace them in the good place.
    temp_files = {}  # contains lists of {dist: (old, new)} paths
    if remove:
        for dist in remove:
            files = dist.get_installed_files()
            temp_files[dist] = move_files(files)
    try:
        if install:
            installed_files = install_dists(install, install_path)  # install to tmp first
        for files in temp_files.itervalues():
            for old, new in files:
                os.remove(new)

    except Exception,e:
        # if an error occurs, put back the files in the good place.
        for files in temp_files.itervalues():
            for old, new in files:
                shutil.move(new, old)


def get_infos(requirements, index=None, installed=None, prefer_final=True):
    """Return the informations on what's going to be installed and upgraded.

    :param requirements: is a *string* containing the requirements for this
                         project (for instance "FooBar 1.1" or "BarBaz (<1.2)")
    :param index: If an index is specified, use this one, otherwise, use
                  :class index.ClientWrapper: to get project metadatas.
    :param installed: a list of already installed distributions.
    :param prefer_final: when picking up the releases, prefer a "final" one
                         over a beta/alpha/etc one.

    The results are returned in a dict, containing all the operations
    needed to install the given requirements::

        >>> get_install_info("FooBar (<=1.2)")
        {'install': [<FooBar 1.1>], 'remove': [], 'conflict': []}

    Conflict contains all the conflicting distributions, if there is a
    conflict.
    """

    if not index:
        index = wrapper.ClientWrapper()

    if not installed:
        installed = get_distributions(use_egg_info=True)

    # Get all the releases that match the requirements
    try:
        releases = index.get_releases(requirements)
    except (ReleaseNotFound, ProjectNotFound), e:
        raise InstallationException('Release not found: "%s"' % requirements)

    # Pick up a release, and try to get the dependency tree
    release = releases.get_last(requirements, prefer_final=prefer_final)

    # Iter since we found something without conflicts
    metadata = release.fetch_metadata()

    # Get the distributions already_installed on the system
    # and add the one we want to install

    distributions = itertools.chain(installed, [release])
    depgraph = generate_graph(distributions)

    # Store all the already_installed packages in a list, in case of rollback.
    infos = {'install': [], 'remove': [], 'conflict': []}

    # Get what the missing deps are
    for dists in depgraph.missing.itervalues():
        if dists:
            logging.info("missing dependencies found, installing them")
            # we have missing deps
            for dist in dists:
                _update_infos(infos, get_infos(dist, index, installed))

    # Fill in the infos
    existing = [d for d in installed if d.name == release.name]
    if existing:
        infos['remove'].append(existing[0])
        infos['conflict'].extend(depgraph.reverse_list[existing[0]])
    infos['install'].append(release)
    return infos


def _update_infos(infos, new_infos):
    """extends the lists contained in the `info` dict with those contained
    in the `new_info` one
    """
    for key, value in infos.iteritems():
        if key in new_infos:
            infos[key].extend(new_infos[key])


def remove(project_name):
    """Removes a single project from the installation"""
    pass




def main(**attrs):
    if 'script_args' not in attrs:
        import sys
        attrs['requirements'] = sys.argv[1]
    get_infos(**attrs)

if __name__ == '__main__':
    main()
