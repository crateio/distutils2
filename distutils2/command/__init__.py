"""Subpackage containing all standard commands."""

from distutils2.errors import PackagingModuleError
from distutils2.util import resolve_name

__all__ = ['get_command_names', 'set_command', 'get_command_class',
           'STANDARD_COMMANDS']

_COMMANDS = {
    'check': 'distutils2.command.check.check',
    'test': 'distutils2.command.test.test',
    'build': 'distutils2.command.build.build',
    'build_py': 'distutils2.command.build_py.build_py',
    'build_ext': 'distutils2.command.build_ext.build_ext',
    'build_clib': 'distutils2.command.build_clib.build_clib',
    'build_scripts': 'distutils2.command.build_scripts.build_scripts',
    'clean': 'distutils2.command.clean.clean',
    'install_dist': 'distutils2.command.install_dist.install_dist',
    'install_lib': 'distutils2.command.install_lib.install_lib',
    'install_headers': 'distutils2.command.install_headers.install_headers',
    'install_scripts': 'distutils2.command.install_scripts.install_scripts',
    'install_data': 'distutils2.command.install_data.install_data',
    'install_distinfo':
        'distutils2.command.install_distinfo.install_distinfo',
    'sdist': 'distutils2.command.sdist.sdist',
    'bdist': 'distutils2.command.bdist.bdist',
    'bdist_dumb': 'distutils2.command.bdist_dumb.bdist_dumb',
    'bdist_wininst': 'distutils2.command.bdist_wininst.bdist_wininst',
    'register': 'distutils2.command.register.register',
    'upload': 'distutils2.command.upload.upload',
    'upload_docs': 'distutils2.command.upload_docs.upload_docs',
}

# XXX use OrderedDict to preserve the grouping (build-related, install-related,
# distribution-related)
STANDARD_COMMANDS = set(_COMMANDS)


def get_command_names():
    """Return registered commands"""
    return sorted(_COMMANDS)


def set_command(location):
    cls = resolve_name(location)
    # XXX we want to do the duck-type checking here
    _COMMANDS[cls.get_command_name()] = cls


def get_command_class(name):
    """Return the registered command"""
    try:
        cls = _COMMANDS[name]
    except KeyError:
        raise PackagingModuleError("Invalid command %s" % name)
    if isinstance(cls, str):
        cls = resolve_name(cls)
        _COMMANDS[name] = cls
    return cls
