from tempfile import mkdtemp
import shutil
import os
import errno
import itertools
import sys
import tarfile

from distutils2 import logger
from distutils2._backport.pkgutil import get_distributions
from distutils2._backport.sysconfig import get_config_var
from distutils2.depgraph import generate_graph
from distutils2.index import wrapper
from distutils2.index.errors import ProjectNotFound, ReleaseNotFound
from distutils2.version import get_version_predicate

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
        yield old, new



# ripped from shutil
def _ensure_directory(path):
    """Ensure that the parent directory of `path` exists"""
    dirname = os.path.dirname(path)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

def _unpack_zipfile(filename, extract_dir):
    try:
        import zipfile
    except ImportError:
        raise ReadError('zlib not supported, cannot unpack this archive.')

    if not zipfile.is_zipfile(filename):
        raise ReadError("%s is not a zip file" % filename)

    zip = zipfile.ZipFile(filename)
    try:
        for info in zip.infolist():
            name = info.filename
            if name.startswith('/') or '..' in name:
                continue

            target = os.path.join(extract_dir, *name.split('/'))
            if not target:
                continue

            _ensure_directory(target)
            if not name.endswith('/'):
                # file
                data = zip.read(info.filename)
                f = open(target,'wb')
                try:
                    f.write(data)
                finally:
                    f.close()
                    del data
    finally:
        zip.close()

def _unpack_tarfile(filename, extract_dir):
    try:
        tarobj = tarfile.open(filename)
    except tarfile.TarError:
        raise ReadError(
            "%s is not a compressed or uncompressed tar file" % filename)
    try:
        tarobj.extractall(extract_dir)
    finally:
        tarobj.close()


_UNPACKERS = (
    (['.tar.gz', '.tgz', '.tar'], _unpack_tarfile),
    (['.zip', '.egg'], _unpack_zipfile))


def _unpack(filename, extract_dir=None):
    if extract_dir is None:
        extract_dir = os.path.dirname(filename)

    for formats, func in _UNPACKERS:
        for format in formats:
            if filename.endswith(format):
                func(filename, extract_dir)
                return extract_dir

    raise ValueError('Unknown archive format: %s' % filename)


def _install_dist(dist, path):
    """Install a distribution into a path"""
    def _run_d1_install(archive_dir, path):
        # backward compat: using setuptools or plain-distutils
        cmd = '%s setup.py install --root=%s --record=%s'
        setup_py = os.path.join(archive_dir, 'setup.py')
        if 'setuptools' in open(setup_py).read():
            cmd += ' --single-version-externally-managed'

        # how to place this file in the egg-info dir
        # for non-distutils2 projects ?
        record_file = os.path.join(archive_dir, 'RECORD')
        os.system(cmd % (sys.executable, path, record_file))
        if not os.path.exists(record_file):
            raise ValueError('Failed to install.')
        return open(record_file).read().split('\n')

    def _run_d2_install(archive_dir, path):
        # using our own install command
        raise NotImplementedError()

    # download
    archive = dist.download()

    # unarchive
    where = _unpack(archive)

    # get into the dir
    archive_dir = None
    for item in os.listdir(where):
        fullpath = os.path.join(where, item)
        if os.path.isdir(fullpath):
            archive_dir = fullpath
            break

    if archive_dir is None:
        raise ValueError('Cannot locate the unpacked archive')

    # install
    old_dir = os.getcwd()
    os.chdir(archive_dir)
    try:
        # distutils2 or distutils1 ?
        if 'setup.py' in os.listdir(archive_dir):
            return _run_d1_install(archive_dir, path)
        else:
            return _run_d2_install(archive_dir, path)
    finally:
        os.chdir(old_dir)


def install_dists(dists, path=None):
    """Install all distributions provided in dists, with the given prefix.

    If an error occurs while installing one of the distributions, uninstall all
    the installed distribution (in the context if this function).

    Return a list of installed files.

    :param dists: distributions to install
    :param path: base path to install distribution in
    """
    if not path:
        path = mkdtemp()

    installed_dists, installed_files = [], []
    for d in dists:
        logger.info('Installing %s %s' % (d.name, d.version))
        try:
            installed_files.extend(_install_dist(d, path))
            installed_dists.append(d)
        except Exception, e :
            logger.info('Failed. %s' % str(e))

            # reverting
            for d in installed_dists:
                _uninstall(d)
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

    except Exception:
        # if an error occurs, put back the files in the good place.
        for files in temp_files.values():
            for old, new in files:
                shutil.move(new, old)

        # now re-raising
        raise

    # we can emove them for good
    for files in temp_files.values():
        for old, new in files:
            os.remove(new)


def _get_setuptools_deps(release):
    # NotImplementedError
    pass


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


    if not installed:
        logger.info('Reading installed distributions')
        installed = get_distributions(use_egg_info=True)

    infos = {'install': [], 'remove': [], 'conflict': []}
    # Is a compatible version of the project is already installed ?
    predicate = get_version_predicate(requirements)
    found = False
    installed = list(installed)
    for installed_project in installed:
        # is it a compatible project ?
        if predicate.name.lower() != installed_project.name.lower():
            continue
        found = True
        logger.info('Found %s %s' % (installed_project.name,
                                     installed_project.metadata.version))
        if predicate.match(installed_project.metadata.version):
            return infos

        break

    if not found:
        logger.info('Project not installed.')

    if not index:
        index = wrapper.ClientWrapper()

    # Get all the releases that match the requirements
    try:
        releases = index.get_releases(requirements)
    except (ReleaseNotFound, ProjectNotFound), e:
        raise InstallationException('Release not found: "%s"' % requirements)

    # Pick up a release, and try to get the dependency tree
    release = releases.get_last(requirements, prefer_final=prefer_final)

    if release is None:
        logger.info('Could not find a matching project')
        return infos

    import pdb; pdb.set_trace()

    # this works for Metadata 1.2
    metadata = release.fetch_metadata()

    # for earlier, we need to build setuptools deps if any
    if 'requires_dist' not in metadata:
        deps = _get_setuptools_deps(release)
    else:
        deps = metadata['requires_dist']

    distributions = itertools.chain(installed, [release])
    depgraph = generate_graph(distributions)

    # Store all the already_installed packages in a list, in case of rollback.
    # Get what the missing deps are
    for dists in depgraph.missing[release]:
        if dists:
            logger.info("missing dependencies found, installing them")
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
    for key, value in infos.items():
        if key in new_infos:
            infos[key].extend(new_infos[key])


def main(**attrs):
    if 'script_args' not in attrs:
        import sys
        attrs['requirements'] = sys.argv[1]
    get_infos(**attrs)


def install(project):
    logger.info('Getting information about "%s".' % project)
    try:
        info = get_infos(project)
    except InstallationException:
        logger.info('Cound not find "%s".' % project)
        return

    if info['install'] == []:
        logger.info('Nothing to install.')
        return

    install_path = get_config_var('base')
    try:
        install_from_infos(info['install'], info['remove'], info['conflict'],
                           install_path=install_path)

    except InstallationConflict, e:
        projects = ['%s %s' % (p.name, p.metadata.version) for p in e.args[0]]
        logger.info('"%s" conflicts with "%s"' % (project, ','.join(projects)))


if __name__ == '__main__':
    main()
