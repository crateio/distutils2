import logging
import xmlrpclib

from distutils2.errors import IrrationalVersionError
from distutils2.index.base import IndexClient
from distutils2.index.errors import ProjectNotFound, InvalidSearchField
from distutils2.index.dist import ReleaseInfo, ReleasesList


PYPI_XML_RPC_URL = 'http://python.org/pypi'

_SEARCH_FIELDS = ['name', 'version', 'author', 'author_email', 'maintainer',
                  'maintainer_email', 'home_page', 'license', 'summary',
                  'description', 'keywords', 'platform', 'download_url']


class Client(IndexClient):
    """Client to query indexes using XML-RPC method calls.
    
    If no server_url is specified, use the default PyPI XML-RPC URL,
    defined in the PYPI_XML_RPC_URL constant::

        >>> client = XMLRPCClient()
        >>> client.server_url == PYPI_XML_RPC_URL
        True

        >>> client = XMLRPCClient("http://someurl/")
        >>> client.server_url
        'http://someurl/'
    """

    def __init__(self, server_url=PYPI_XML_RPC_URL, prefer_final=False):
        self.server_url = server_url
        self._projects = {}
        self._prefer_final = prefer_final

    def _search_for_releases(self, requirements):
        return self.get_releases(requirements.name)
    
    def _get_release(self, requirements, prefer_final=False):
        releases = self.get_releases(requirements.name)
        release = releases.get_last(requirements, prefer_final)
        self.get_metadata(release.name, "%s" % release.version)
        self.get_distributions(release.name, "%s" % release.version)
        return release

    @property
    def proxy(self):
        """Property used to return the XMLRPC server proxy.

        If no server proxy is defined yet, creates a new one::

            >>> client = XmlRpcClient()
            >>> client.proxy()
            <ServerProxy for python.org/pypi>

        """
        if not hasattr(self, '_server_proxy'):
            self._server_proxy = xmlrpclib.ServerProxy(self.server_url)

        return self._server_proxy

    def _get_project(self, project_name):
        """Return an project instance, create it if necessary"""
        return self._projects.setdefault(project_name,
                                         ReleasesList(project_name))

    def get_releases(self, project_name, show_hidden=True, force_update=False):
        """Return the list of existing releases for a specific project.

        Cache the results from one call to another.

        If show_hidden is True, return the hidden releases too.
        If force_update is True, reprocess the index to update the
        informations (eg. make a new XML-RPC call).
        ::

            >>> client = XMLRPCClient()
            >>> client.get_releases('Foo')
            ['1.1', '1.2', '1.3']

        If no such project exists, raise a ProjectNotFound exception::

            >>> client.get_project_versions('UnexistingProject')
            ProjectNotFound: UnexistingProject

        """
        def get_versions(project_name, show_hidden):
            return self.proxy.package_releases(project_name, show_hidden)

        if not force_update and (project_name in self._projects):
            project = self._projects[project_name]
            if not project.contains_hidden and show_hidden:
                # if hidden releases are requested, and have an existing
                # list of releases that does not contains hidden ones
                all_versions = get_versions(project_name, show_hidden)
                existing_versions = project.get_versions()
                hidden_versions = list(set(all_versions) -
                                       set(existing_versions))
                for version in hidden_versions:
                    project.add_release(release=ReleaseInfo(project_name,
                                                            version))
            return project
        else:
            versions = get_versions(project_name, show_hidden)
            if not versions:
                raise ProjectNotFound(project_name)
            project = self._get_project(project_name)
            project.add_releases([ReleaseInfo(project_name, version) 
                                  for version in versions])
            return project

    def get_distributions(self, project_name, version):
        """Grab informations about distributions from XML-RPC.

        Return a ReleaseInfo object, with distribution-related informations
        filled in.
        """
        url_infos = self.proxy.release_urls(project_name, version)
        project = self._get_project(project_name)
        if version not in project.get_versions():
            project.add_release(release=ReleaseInfo(project_name, version))
        release = project.get_release(version)
        for info in url_infos:
            packagetype = info['packagetype']
            dist_infos = {'url': info['url'],
                          'hashval': info['md5_digest'],
                          'hashname': 'md5',
                          'is_external': False}
            release.add_distribution(packagetype, **dist_infos)
        return release

    def get_metadata(self, project_name, version):
        """Retreive project metadatas.

        Return a ReleaseInfo object, with metadata informations filled in.
        """
        metadata = self.proxy.release_data(project_name, version)
        project = self._get_project(project_name)
        if version not in project.get_versions():
            project.add_release(release=ReleaseInfo(project_name, version))
        release = project.get_release(version)
        release.set_metadata(metadata)
        return release

    def search(self, name=None, operator="or", **kwargs):
        """Find using the keys provided in kwargs.
        
        You can set operator to "and" or "or".
        """
        for key in kwargs:
            if key not in _SEARCH_FIELDS:
                raise InvalidSearchField(key)
        if name:
            kwargs["name"] = name
        projects = self.proxy.search(kwargs, operator)
        for p in projects:
            project = self._get_project(p['name'])
            try:
                project.add_release(release=ReleaseInfo(p['name'], 
                    p['version'], metadata={'summary':p['summary']}))
            except IrrationalVersionError, e:
                logging.warn("Irrational version error found: %s" % e)
        
        return [self._projects[p['name']] for p in projects]
