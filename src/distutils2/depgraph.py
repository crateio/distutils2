"""
A dependency graph generator. The graph is represented as an instance of
:class:`DependencyGraph`, and DOT output is possible as well.
"""

from distutils2._backport import pkgutil
from distutils2.errors import DistutilsError
from distutils2.version import VersionPredicate

__all__ = ['DependencyGraph', 'generate_graph']


class DependencyGraph(object):
    """
    Represents a dependency graph between distributions.

    The depedency relationships are stored in an *adjacency_list* that maps
    distributions to a list of ``(other, label)`` tuples where  ``other``
    is a distribution and the edge is labelled with ``label`` (i.e. the version
    specifier, if such was provided). If any missing depencies are found,
    they are stored in ``missing``. It maps distributions to a list of
    requirements that were not provided by any other distributions.
    """

    def __init__(self):
        self.adjacency_list = {}
        self.missing = {}

    def add_distribution(self, distribution):
        """
        Add distribution *x* to the graph.

        :type distribution: :class:`pkgutil.Distribution` or
                            :class:`pkgutil.EggInfoDistribution`
        """
        self.adjacency_list[distribution] = list()
        self.missing[distribution] = list()

    def add_edge(self, x, y, label=None):
        """
        Add an edge from distribution *x* to distribution *y* with the given
        *label*.


        :type x: :class:`pkgutil.Distribution` or
                 :class:`pkgutil.EggInfoDistribution`
        :type y: :class:`pkgutil.Distribution` or
                 :class:`pkgutil.EggInfoDistribution`
        :type label: ``str`` or ``None``
        """
        self.adjacency_list[x].append((y, label))

    def add_missing(self, distribution, requirement):
        """
        Add a missing *requirement* for the given *distribution*.

        :type distribution: :class:`pkgutil.Distribution` or
                            :class:`pkgutil.EggInfoDistribution`
        :type requirement: ``str``
        """
        self.missing[distribution].append(requirement)


def graph_to_dot(graph, f, skip_disconnected=True):
    """
    Writes a DOT output for the graph to the provided *file*.
    If *skip_disconnected* is set to ``True``, then all distributions
    that are not dependent on any other distributions are skipped.

    :type f: ``file``
    ;type skip_disconnected: ``bool``
    """
    if not isinstance(f, file):
        raise TypeError('the argument has to be of type file')

    disconnected = []

    f.write("digraph dependencies {\n")
    for dist, adjs in graph.adjacency_list.iteritems():
        if len(adjs) == 0 and not skip_disconnected:
            disconnected.append(dist)
        for (other, label) in adjs:
            if not label is None:
                f.write('"%s" -> "%s" [label="%s"]\n' %
                                            (dist.name, other.name, label))
            else:
                f.write('"%s" -> "%s"\n' % (dist.name, other.name))
    if not skip_disconnected and len(disconnected) > 0:
        f.write('subgraph disconnected {\n')
        f.write('label = "Disconnected"\n')
        f.write('bgcolor = red\n')

        for dist in disconnected:
            f.write('"%s"' % dist.name)
            f.write('\n')
        f.write('}\n')
    f.write('}\n')


def generate_graph(dists):
    """
    Generates a dependency graph from the given distributions.

    :parameter dists: a list of distributions
    :type dists: list of :class:`pkgutil.Distribution` and
                         :class:`pkgutil.EggInfoDistribution` instances
    :rtype: an :class:`DependencyGraph` instance
    """
    graph = DependencyGraph()
    provided = {} # maps names to lists of (version, dist) tuples

    dists = list(dists) # maybe use generator_tools in future

    missing = [] # a list of (instance, requirement) tuples

    # first, build the graph and find out the provides
    for dist in dists:
        graph.add_distribution(dist)
        provides = dist.metadata['Provides-Dist'] + dist.metadata['Provides']

        for p in provides:
            comps = p.split(" ", 1)
            name = comps[0]
            version = None
            if len(comps) == 2:
                version = comps[1]
                if len(version) < 3 or version[0] != '(' or version[-1] != ')':
                    raise DistutilsError('Distribution %s has ill formed' \
                                         'provides field: %s' % (dist.name, p))
                version = version[1:-1] # trim off parenthesis
            if not name in provided:
                provided[name] = []
            provided[name].append((version, dist))

    # now make the edges
    for dist in dists:
        requires = dist.metadata['Requires-Dist'] + dist.metadata['Requires']
        for req in requires:
            predicate = VersionPredicate(req)
            comps = req.split(" ", 1)
            name = comps[0]

            if not name in provided:
                graph.add_missing(dist, req)
            else:
                for (version, provider) in provided[name]:
                    if predicate.match(version):
                        graph.add_edge(dist, provider, req)

    return graph


def dependent_dists(dists, dist):
    """
    Recursively generate a list of distributions from *dists* that are
    dependent on *dist*.

    :param dists: a list of distributions
    :param dist: a distribution, member of *dists* for which we are interested
    """
    if not dist in dists:
        raise ValueError('The given distribution is not a member of the list')
    graph = generate_graph(dists)

    dep = [dist]
    fringe = [dist] # list of nodes we should expand
    while not len(fringe) == 0:
        next = graph.adjacency_list[fringe.pop()]
        for (dist, label) in next:
            if not dist in dep: # avoid infinite loops
                dep.append(dist)
                fringe.append(dist)

    dep.pop()
    return dep

if __name__ == '__main__':
    dists = list(pkgutil.get_distributions(use_egg_info=True))
    graph = generate_graph(dists)
    for dist, reqs in graph.missing.iteritems():
        if len(reqs) > 0:
            print("Missing dependencies for %s: %s" % (dist.name,
                                                       ", ".join(reqs)))
    f = open('output.dot', 'w')
    graph.to_dot(f, True)
