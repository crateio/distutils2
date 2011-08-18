"""Class and functions dealing with dependencies between distributions.

This module provides a DependencyGraph class to represent the
dependencies between distributions.  Auxiliary functions can generate a
graph, find reverse dependencies, and print a graph in DOT format.
"""

import sys

from StringIO import StringIO
from distutils2.errors import PackagingError
from distutils2.version import VersionPredicate, IrrationalVersionError

__all__ = ['DependencyGraph', 'generate_graph', 'dependent_dists',
           'graph_to_dot']


class DependencyGraph:
    """
    Represents a dependency graph between distributions.

    The dependency relationships are stored in an ``adjacency_list`` that maps
    distributions to a list of ``(other, label)`` tuples where  ``other``
    is a distribution and the edge is labeled with ``label`` (i.e. the version
    specifier, if such was provided). Also, for more efficient traversal, for
    every distribution ``x``, a list of predecessors is kept in
    ``reverse_list[x]``. An edge from distribution ``a`` to
    distribution ``b`` means that ``a`` depends on ``b``. If any missing
    dependencies are found, they are stored in ``missing``, which is a
    dictionary that maps distributions to a list of requirements that were not
    provided by any other distributions.
    """

    def __init__(self):
        self.adjacency_list = {}
        self.reverse_list = {}
        self.missing = {}

    def add_distribution(self, distribution):
        """Add the *distribution* to the graph.

        :type distribution: :class:`distutils2.database.Distribution` or
                            :class:`distutils2.database.EggInfoDistribution`
        """
        self.adjacency_list[distribution] = []
        self.reverse_list[distribution] = []
        self.missing[distribution] = []

    def add_edge(self, x, y, label=None):
        """Add an edge from distribution *x* to distribution *y* with the given
        *label*.

        :type x: :class:`distutils2.database.Distribution` or
                 :class:`distutils2.database.EggInfoDistribution`
        :type y: :class:`distutils2.database.Distribution` or
                 :class:`distutils2.database.EggInfoDistribution`
        :type label: ``str`` or ``None``
        """
        self.adjacency_list[x].append((y, label))
        # multiple edges are allowed, so be careful
        if x not in self.reverse_list[y]:
            self.reverse_list[y].append(x)

    def add_missing(self, distribution, requirement):
        """
        Add a missing *requirement* for the given *distribution*.

        :type distribution: :class:`distutils2.database.Distribution` or
                            :class:`distutils2.database.EggInfoDistribution`
        :type requirement: ``str``
        """
        self.missing[distribution].append(requirement)

    def _repr_dist(self, dist):
        return '%r %s' % (dist.name, dist.version)

    def repr_node(self, dist, level=1):
        """Prints only a subgraph"""
        output = []
        output.append(self._repr_dist(dist))
        for other, label in self.adjacency_list[dist]:
            dist = self._repr_dist(other)
            if label is not None:
                dist = '%s [%s]' % (dist, label)
            output.append('    ' * level + str(dist))
            suboutput = self.repr_node(other, level + 1)
            subs = suboutput.split('\n')
            output.extend(subs[1:])
        return '\n'.join(output)

    def __repr__(self):
        """Representation of the graph"""
        output = []
        for dist, adjs in self.adjacency_list.items():
            output.append(self.repr_node(dist))
        return '\n'.join(output)


def graph_to_dot(graph, f, skip_disconnected=True):
    """Writes a DOT output for the graph to the provided file *f*.

    If *skip_disconnected* is set to ``True``, then all distributions
    that are not dependent on any other distribution are skipped.

    :type f: has to support ``file``-like operations
    :type skip_disconnected: ``bool``
    """
    disconnected = []

    f.write(u"digraph dependencies {\n")
    for dist, adjs in graph.adjacency_list.items():
        if len(adjs) == 0 and not skip_disconnected:
            disconnected.append(dist)
        for other, label in adjs:
            if not label is None:
                f.write(u'"%s" -> "%s" [label="%s"]\n' %
                                            (dist.name, other.name, label))
            else:
                f.write(u'"%s" -> "%s"\n' % (dist.name, other.name))
    if not skip_disconnected and len(disconnected) > 0:
        f.write(u'subgraph disconnected {\n')
        f.write(u'label = "Disconnected"\n')
        f.write(u'bgcolor = red\n')

        for dist in disconnected:
            f.write(u'"%s"' % dist.name)
            f.write(u'\n')
        f.write(u'}\n')
    f.write(u'}\n')


def generate_graph(dists):
    """Generates a dependency graph from the given distributions.

    :parameter dists: a list of distributions
    :type dists: list of :class:`distutils2.database.Distribution` and
                 :class:`distutils2.database.EggInfoDistribution` instances
    :rtype: a :class:`DependencyGraph` instance
    """
    graph = DependencyGraph()
    provided = {}  # maps names to lists of (version, dist) tuples

    # first, build the graph and find out the provides
    for dist in dists:
        graph.add_distribution(dist)
        provides = (dist.metadata['Provides-Dist'] +
                    dist.metadata['Provides'] +
                    ['%s (%s)' % (dist.name, dist.version)])

        for p in provides:
            comps = p.strip().rsplit(" ", 1)
            name = comps[0]
            version = None
            if len(comps) == 2:
                version = comps[1]
                if len(version) < 3 or version[0] != '(' or version[-1] != ')':
                    raise PackagingError('distribution %r has ill-formed'
                                         'provides field: %r' % (dist.name, p))
                version = version[1:-1]  # trim off parenthesis
            if name not in provided:
                provided[name] = []
            provided[name].append((version, dist))

    # now make the edges
    for dist in dists:
        requires = dist.metadata['Requires-Dist'] + dist.metadata['Requires']
        for req in requires:
            try:
                predicate = VersionPredicate(req)
            except IrrationalVersionError:
                # XXX compat-mode if cannot read the version
                name = req.split()[0]
                predicate = VersionPredicate(name)

            name = predicate.name

            if name not in provided:
                graph.add_missing(dist, req)
            else:
                matched = False
                for version, provider in provided[name]:
                    try:
                        match = predicate.match(version)
                    except IrrationalVersionError:
                        # XXX small compat-mode
                        if version.split(' ') == 1:
                            match = True
                        else:
                            match = False

                    if match:
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
    if dist not in dists:
        raise ValueError('given distribution %r is not a member of the list' %
                         dist.name)
    graph = generate_graph(dists)

    dep = [dist]  # dependent distributions
    fringe = graph.reverse_list[dist]  # list of nodes we should inspect

    while not len(fringe) == 0:
        node = fringe.pop()
        dep.append(node)
        for prev in graph.reverse_list[node]:
            if prev not in dep:
                fringe.append(prev)

    dep.pop(0)  # remove dist from dep, was there to prevent infinite loops
    return dep


def main():
    from distutils2.database import get_distributions
    tempout = StringIO()
    try:
        old = sys.stderr
        sys.stderr = tempout
        try:
            dists = list(get_distributions(use_egg_info=True))
            graph = generate_graph(dists)
        finally:
            sys.stderr = old
    except Exception:
        e = sys.exc_info()[1]
        tempout.seek(0)
        tempout = tempout.read()
        print(u'Could not generate the graph')
        print(tempout)
        print(e)
        sys.exit(1)

    for dist, reqs in graph.missing.items():
        if len(reqs) > 0:
            print(u"Warning: Missing dependencies for %r:" % dist.name,
                  ", ".join(reqs))
    # XXX replace with argparse
    if len(sys.argv) == 1:
        print(u'Dependency graph:')
        print(u'   ', repr(graph).replace(u'\n', u'\n    '))
        sys.exit(0)
    elif len(sys.argv) > 1 and sys.argv[1] in ('-d', '--dot'):
        if len(sys.argv) > 2:
            filename = sys.argv[2]
        else:
            filename = 'depgraph.dot'

        with open(filename, 'w') as f:
            graph_to_dot(graph, f, True)
        tempout.seek(0)
        tempout = tempout.read()
        print(tempout)
        print('Dot file written at %r' % filename)
        sys.exit(0)
    else:
        print('Supported option: -d [filename]')
        sys.exit(1)


if __name__ == '__main__':
    main()
