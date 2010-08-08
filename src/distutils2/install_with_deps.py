import logging
from distutils2.index import wrapper
from distutils2.index.errors import ProjectNotFound, ReleaseNotFound
from distutils2.depgraph import generate_graph
from distutils2._backport.pkgutil import get_distributions


"""Provides installations scripts.

The goal of this script is to install a release from the indexes (eg.
PyPI), including the dependencies of the releases if needed.

It uses the work made in pkgutil and by the index crawlers to browse the
installed distributions, and rely on the instalation commands to install.
"""


def get_deps(requirements, index):
    """Return the dependencies of a project, as a depgraph object.

    Build a :class depgraph.DependencyGraph: for the given requirements

    If the project does not uses Metadata < 1.1, dependencies can't be handled
    from here, so it returns an empty list of dependencies.

    :param requirements: is a string containing the version predicate to take
                         the project name and version specifier from.
    :param index: the index to use for making searches.
    """
    deps = []
    release = index.get_release(requirements)
    requires = release.metadata['Requires-Dist'] + release.metadata['Requires']
    deps.append(release) # include the release we are computing deps.
    for req in requires:
        deps.extend(get_deps(req, index))
    return deps


def install(requirements, index=None, interactive=True, upgrade=True,
            prefer_source=True, prefer_final=True):
    """Given a list of distributions to install, a list of distributions to
    remove, and a list of conflicts, proceed and do what's needed to be done.

    :param requirements: is a *string* containing the requirements for this
                         project (for instance "FooBar 1.1" or "BarBaz (<1.2)
    :param index: If an index is specified, use this one, otherwise, use
                  :class index.ClientWrapper: to get project metadatas.
    :param interactive: if set to True, will prompt the user for interactions
                        of needed. If false, use the default values.
    :param upgrade: If a project exists in a newer version, does the script
                    need to install the new one, or keep the already installed
                    version.
    :param prefer_source: used to tell if the user prefer source distributions
                          over built dists.
    :param prefer_final: if set to true, pick up the "final" versions (eg.
                         stable) over the beta, alpha (not final) ones.
    """
    # get the default index if none is specified
    if not index:
        index = wrapper.WrapperClient()

    # check if the project is already installed.
    installed_release = get_installed_release(requirements)

    # if a version that satisfy the requirements is already installed
    if installed_release and (interactive or upgrade):
        new_releases = index.get_releases(requirements)
        if (new_releases.get_last(requirements).version >
            installed_release.version):
            if interactive:
                # prompt the user to install the last version of the package.
                # set upgrade here.
                print "You want to install a package already installed on your"
                "system. A new version exists, you could just use the version"
                "you have, or upgrade to the latest version"

                upgrade = raw_input("Do you want to install the most recent one ? (Y/n)") or "Y"
                if upgrade in ('Y', 'y'):
                    upgrade = True
                else:
                    upgrade = False
            if not upgrade:
                return

    # create the depgraph from the dependencies of the release we want to
    # install
    graph = generate_graph(get_deps(requirements, index))
    from ipdb import set_trace
    set_trace()
    installed = [] # to uninstall on errors
    try:
        for release in graph.adjacency_list:
            dist = release.get_distribution()
            install(dist)
            installed.append(dist)
            print "%s have been installed on your system" % requirements
    except:
        print "an error has occured, uninstalling"
        for dist in installed:
            uninstall_dist(dist)

class InstallationException(Exception):
    pass

def get_install_info(requirements, index=None, already_installed=None):
    """Return the informations on what's going to be installed and upgraded.

    :param requirements: is a *string* containing the requirements for this
                         project (for instance "FooBar 1.1" or "BarBaz (<1.2)")
    :param index: If an index is specified, use this one, otherwise, use
                  :class index.ClientWrapper: to get project metadatas.
    :param already_installed: a list of already installed distributions.

    The results are returned in a dict. For instance::

        >>> get_install_info("FooBar (<=1.2)")
        {'install': [<FooBar 1.1>], 'remove': [], 'conflict': []}

    Conflict contains all the conflicting distributions, if there is a
    conflict.

    """
    def update_infos(new_infos, infos):
        for key, value in infos.items():
            if key in new_infos:
                infos[key].extend(new_infos[key])
        return new_infos

    if not index:
        index = wrapper.ClientWrapper()
    logging.info("searching releases for %s" % requirements)

    # 1. get all the releases that match the requirements
    try:
        releases = index.get_releases(requirements)
    except (ReleaseNotFound, ProjectNotFound), e:
       raise InstallationException('Release not found: "%s"' % requirements)

    # 2. pick up a release, and try to get the dependency tree
    release = releases.get_last(requirements)
    metadata = release.fetch_metadata()

    # 3. get the distributions already_installed on the system
    # 4. and add the one we want to install
    if not already_installed:
        already_installed = get_distributions()

    logging.info("fetching %s %s dependencies" % (
                 release.name, release.version))
    distributions = already_installed + [release]
    depgraph = generate_graph(distributions)

    # store all the already_installed packages in a list, in case of rollback.
    infos = {'install':[], 'remove': [], 'conflict': []}

    # 5. get what the missing deps are
    for dists in depgraph.missing.values():
        if dists:
            logging.info("missing dependencies found, installing them")
            # we have missing deps
            for dist in dists:
                update_infos(get_install_info(dist, index, already_installed),
                             infos)

    # 6. fill in the infos
    existing = [d for d in already_installed if d.name == release.name]
    if existing:
        infos['remove'].append(existing[0])
        infos['conflict'].extend(depgraph.reverse_list[existing[0]])
    infos['install'].append(release)
    return infos
