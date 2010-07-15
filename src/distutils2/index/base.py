from distutils2.version import VersionPredicate
from distutils2.index.errors import DistributionNotFound


class IndexClient(object):
    """Base class containing common index client methods"""

    def _search_for_releases(self, requirements):
        """To be redefined in child classes"""
        return NotImplemented

    def find(self, requirements, prefer_final=None):
        """Browse the PyPI to find distributions that fullfil the given
        requirements.

        :param requirements: A project name and it's distribution, using
                             version specifiers, as described in PEP345.
        :type requirements:  You can pass either a version.VersionPredicate
                             or a string.
        :param prefer_final: if the version is not mentioned in requirements,
                             and the last version is not a "final" one
                             (alpha, beta, etc.), pick up the last final
                             version.
        """
        requirements = self._get_version_predicate(requirements)
        prefer_final = self._get_prefer_final(prefer_final)

        # internally, rely on the "_search_for_release" method
        dists = self._search_for_releases(requirements)
        if dists:
            dists = dists.filter(requirements)
            dists.sort_releases(prefer_final=prefer_final)
        return dists

    def get(self, requirements, prefer_final=None):
        """Return only one release that fulfill the given requirements.

        :param requirements: A project name and it's distribution, using
                             version specifiers, as described in PEP345.
        :type requirements:  You can pass either a version.VersionPredicate
                             or a string.
        :param prefer_final: if the version is not mentioned in requirements,
                             and the last version is not a "final" one
                             (alpha, beta, etc.), pick up the last final
                             version.
        """
        predicate = self._get_version_predicate(requirements)

        # internally, rely on the "_get_release" method
        dist = self._get_release(predicate, prefer_final=prefer_final)
        if not dist:
            raise DistributionNotFound(requirements)
        return dist

    def download(self, requirements, temp_path=None, prefer_final=None,
                 prefer_source=True):
        """Download the distribution, using the requirements.

        If more than one distribution match the requirements, use the last
        version.
        Download the distribution, and put it in the temp_path. If no temp_path
        is given, creates and return one.

        Returns the complete absolute path to the downloaded archive.

        :param requirements: The same as the find attribute of `find`.

        You can specify prefer_final argument here. If not, the default 
        one will be used.
        """
        return self.get(requirements, prefer_final)\
                   .download(prefer_source=prefer_source, path=temp_path)

    def _get_version_predicate(self, requirements):
        """Return a VersionPredicate object, from a string or an already
        existing object.
        """
        if isinstance(requirements, str):
            requirements = VersionPredicate(requirements)
        return requirements

    def _get_prefer_final(self, prefer_final=None):
        """Return the prefer_final bit parameter or the specified one if
        exists."""
        if prefer_final:
            return prefer_final
        else:
            return self._prefer_final
