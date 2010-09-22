""" distutil2.config

    Know how to read all config files Distutils2 uses.
"""
import os
import sys
from ConfigParser import RawConfigParser

from distutils2 import log
from distutils2.util import check_environ


class Config(object):
    """Reads configuration files and work with the Distribution instance
    """
    def __init__(self, dist):
        self.dist = dist
        self.setup_hook = None

    def run_hook(self):
        if self.setup_hook is None:
            return
        # transform the hook name into a callable
        # then run it !
        # XXX

    def find_config_files(self):
        """Find as many configuration files as should be processed for this
        platform, and return a list of filenames in the order in which they
        should be parsed.  The filenames returned are guaranteed to exist
        (modulo nasty race conditions).

        There are three possible config files: distutils.cfg in the
        Distutils installation directory (ie. where the top-level
        Distutils __inst__.py file lives), a file in the user's home
        directory named .pydistutils.cfg on Unix and pydistutils.cfg
        on Windows/Mac; and setup.cfg in the current directory.

        The file in the user's home directory can be disabled with the
        --no-user-cfg option.
        """
        files = []
        check_environ()

        # Where to look for the system-wide Distutils config file
        sys_dir = os.path.dirname(sys.modules['distutils2'].__file__)

        # Look for the system config file
        sys_file = os.path.join(sys_dir, "distutils.cfg")
        if os.path.isfile(sys_file):
            files.append(sys_file)

        # What to call the per-user config file
        if os.name == 'posix':
            user_filename = ".pydistutils.cfg"
        else:
            user_filename = "pydistutils.cfg"

        # And look for the user config file
        if self.dist.want_user_cfg:
            user_file = os.path.join(os.path.expanduser('~'), user_filename)
            if os.path.isfile(user_file):
                files.append(user_file)

        # All platforms support local setup.cfg
        local_file = "setup.cfg"
        if os.path.isfile(local_file):
            files.append(local_file)

        log.debug("using config files: %s" % ', '.join(files))
        return files

    def _convert_metadata(self, name, value):
        # converts a value found in setup.cfg into a valid metadata
        # XXX
        return value

    def _read_metadata(self, parser):
        if parser.has_option('global', 'setup_hook'):
            self.setup_hook = parser.get('global', 'setup_hook')

        metadata = self.dist.metadata
        # setting the metadata values
        if 'metadata' in parser.sections():
            for key, value in parser.items('metadata'):
                if metadata.is_metadata_field(key):
                    metadata[key] = self._convert_metadata(key, value)

    def parse_config_files(self, filenames=None):
        if filenames is None:
            filenames = self.find_config_files()

        log.debug("Distribution.parse_config_files():")

        parser = RawConfigParser()
        for filename in filenames:
            log.debug("  reading %s" % filename)
            parser.read(filename)

            if os.path.split(filename)[-1] == 'setup.cfg':
                self._read_metadata(parser)

            for section in parser.sections():
                options = parser.options(section)
                opt_dict = self.dist.get_option_dict(section)

                for opt in options:
                    if opt != '__name__':
                        val = parser.get(section, opt)
                        opt = opt.replace('-', '_')


                        # XXX this is not used ...

                        # Hooks use a suffix system to prevent being overriden
                        # by a config file processed later (i.e. a hook set in
                        # the user config file cannot be replaced by a hook
                        # set in a project config file, unless they have the
                        # same suffix).
                        if (opt.startswith("pre_hook.") or
                            opt.startswith("post_hook.")):
                            hook_type, alias = opt.split(".")
                            hook_dict = opt_dict.setdefault(hook_type,
                                                            (filename, {}))[1]
                            hook_dict[alias] = val
                        else:
                            opt_dict[opt] = (filename, val)

            # Make the RawConfigParser forget everything (so we retain
            # the original filenames that options come from)
            parser.__init__()

        # If there was a "global" section in the config file, use it
        # to set Distribution options.
        if 'global' in self.dist.command_options:
            for (opt, (src, val)) in self.dist.command_options['global'].items():
                alias = self.dist.negative_opt.get(opt)
                try:
                    if alias:
                        setattr(self.dist, alias, not strtobool(val))
                    elif opt in ('verbose', 'dry_run'):  # ugh!
                        setattr(self.dist, opt, strtobool(val))
                    else:
                        setattr(self.dist, opt, val)
                except ValueError, msg:
                    raise DistutilsOptionError(msg)
