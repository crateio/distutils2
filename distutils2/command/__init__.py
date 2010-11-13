"""distutils.command

Package containing implementation of all the standard Distutils
commands."""
from distutils2.errors import DistutilsModuleError
from distutils2.util import resolve_name

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
    'upload_docs': 'distutils2.command.upload_docs.upload_docs'}


def get_command_names():
    """Returns registered commands"""
    return sorted(_COMMANDS.keys())


def set_command(location):
    klass = resolve_name(location)
    # we want to do the duck-type checking here
    # XXX
    _COMMANDS[klass.get_command_name()] = klass


def get_command_class(name):
    """Return the registered command"""
    try:
        klass = _COMMANDS[name]
        if isinstance(klass, str):
            klass = resolve_name(klass)
            _COMMANDS[name] = klass
        return klass
    except KeyError:
        raise DistutilsModuleError("Invalid command %s" % name)
