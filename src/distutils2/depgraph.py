"""Analyse the relationships between the distributions in the system and generate
a dependency graph.
"""

from distutils2.errors import DistutilsError
from distutils2.version import VersionPredicate

__all__ = ['DependencyGraph', 'generate_graph', 'dependent_dists',
           'graph_to_dot']


class DependencyGraph(object):
    """
    Represents a dependency graph between distributions.

    The dependency relationships are stored in an ``adjacency_list`` that maps
    distributions to a list of ``(other, label)`` tuples where  ``other``
    is a distribution and the edge is labelled with ``label`` (i.e. the version
    specifier, if such was provided). Also, for more efficient traversal, for
    every distribution ``x``, a list of predecessors is kept in
    ``reverse_list[x]``. An edge from distribution ``a`` to
    distribution ``b`` means that ``a`` depends on ``b``. If any missing
    depencies are found, they are stored in ``missing``, which is a dictionary
    that maps distributions to a list of requirements that were not provided by
    any other distributions.
    """

    def __init__(self):
        self.adjacency_list = {}
        self.reverse_list = {}
        self.missing = {}

    def add_distribution(self, distribution):
        """Add the *distribution* to the graph.

        :type distribution: :class:`pkgutil.Distribution` or
                            :class:`pkgutil.EggInfoDistribution`
        """
        self.adjacency_list[distribution] = list()
        self.reverse_list[distribution] = list()
        self.missing[distribution] = list()

    def add_edge(self, x, y, label=None):
        """Add an edge from distribution *x* to distribution *y* with the given
        *label*.

        :type x: :class:`pkgutil.Distribution` or
                 :class:`pkgutil.EggInfoDistribution`
        :type y: :class:`pkgutil.Distribution` or
                 :class:`pkgutil.EggInfoDistribution`
        :type label: ``str`` or ``None``
        """
        self.adjacency_list[x].append((y, label))
        # multiple edges are allowed, so be careful
        if not x in self.reverse_list[y]:
            self.reverse_list[y].append(x)

    def add_missing(self, distribution, requirement):
        """
        Add a missing *requirement* for the given *distribution*.

        :type distribution: :class:`pkgutil.Distribution` or
                            :class:`pkgutil.EggInfoDistribution`
        :type requirement: ``str``
        """
        self.missing[distribution].append(requirement)


def graph_to_dot(graph, f, skip_disconnected=True):
    """Writes a DOT output for the graph to the provided file *f*.

    If *skip_disconnected* is set to ``True``, then all distributions
    that are not dependent on any other distribution are skipped.

    :type f: has to support ``file``-like operations
    :type skip_disconnected: ``bool``
    """
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
    """Generates a dependency graph from the given distributions.

    :parameter dists: a list of distributions
    :type dists: list of :class:`pkgutil.Distribution` and
                         :class:`pkgutil.EggInfoDistribution` instances
    :rtype: an :class:`DependencyGraph` instance
    """
    graph = DependencyGraph()
    provided = {} # maps names to lists of (version, dist) tuples
    dists = list(dists) # maybe use generator_tools in future

    # first, build the graph and find out the provides
    for dist in dists:
        graph.add_distribution(dist)
        provides = dist.metadata['Provides-Dist'] + dist.metadata['Provides']

        for p in provides:
            comps = p.strip().rsplit(" ", 1)
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
            name = predicate.name

            if not name in provided:
                graph.add_missing(dist, req)
            else:
                matched = False
                for (version, provider) in provided[name]:
                    if predicate.match(version):
                        graph.add_edge(dist, provider, req)
                        matched = True
                        break
                if not matched:
                    graph.add_missing(dist, req)

    return graph


def dependent_dists(dists, dist):
    """Recursively generate a list of distributions from *dists* that are
    dependent on *dist*.

    :param dists: a list of distributions
    :param dist: a distribution, member of *dists* for which we are interested
    """
    if not dist in dists:
        raise ValueError('The given distribution is not a member of the list')
    graph = generate_graph(dists)

    dep = [dist] # dependent distributions
    fringe = graph.reverse_list[dist] # list of nodes we should inspect

    while not len(fringe) == 0:
        node = fringe.pop()
        dep.append(node)
        for prev in graph.reverse_list[node]:
            if not prev in dep:
                fringe.append(prev)

    dep.pop(0) # remove dist from dep, was there to prevent infinite loops
    return dep

if __name__ == '__main__':
    from distutils2._backport.pkgutil import get_distributions
    dists = list(get_distributions(use_egg_info=True))
    graph = generate_graph(dists)
    for dist, reqs in graph.missing.iteritems():
        if len(reqs) > 0:
            print("Missing dependencies for %s: %s" % (dist.name,
                                                       ", ".join(reqs)))
    f = open('output.dot', 'w')
    graph_to_dot(graph, f, True)
