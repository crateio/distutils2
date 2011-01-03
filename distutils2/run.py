import os
import sys
from optparse import OptionParser
import logging

from distutils2 import logger
from distutils2.util import grok_environment_error
from distutils2.errors import (DistutilsSetupError, DistutilsArgError,
                               DistutilsError, CCompilerError)
from distutils2.dist import Distribution
from distutils2 import __version__
from distutils2._backport.pkgutil import get_distributions, get_distribution
from distutils2.depgraph import generate_graph
from distutils2.install import install

# This is a barebones help message generated displayed when the user
# runs the setup script with no arguments at all.  More useful help
# is generated with various --help options: global help, list commands,
# and per-command help.
USAGE = """\
usage: %(script)s [global_opts] cmd1 [cmd1_opts] [cmd2 [cmd2_opts] ...]
   or: %(script)s --help [cmd1 cmd2 ...]
   or: %(script)s --help-commands
   or: %(script)s cmd --help
"""


def gen_usage(script_name):
    script = os.path.basename(script_name)
    return USAGE % {'script': script}


def commands_main(**attrs):
    """The gateway to the Distutils: do everything your setup script needs
    to do, in a highly flexible and user-driven way.  Briefly: create a
    Distribution instance; find and parse config files; parse the command
    line; run each Distutils command found there, customized by the options
    supplied to 'setup()' (as keyword arguments), in config files, and on
    the command line.

    The Distribution instance might be an instance of a class supplied via
    the 'distclass' keyword argument to 'setup'; if no such class is
    supplied, then the Distribution class (in dist.py) is instantiated.
    All other arguments to 'setup' (except for 'cmdclass') are used to set
    attributes of the Distribution instance.

    The 'cmdclass' argument, if supplied, is a dictionary mapping command
    names to command classes.  Each command encountered on the command line
    will be turned into a command class, which is in turn instantiated; any
    class found in 'cmdclass' is used in place of the default, which is
    (for command 'foo_bar') class 'foo_bar' in module
    'distutils2.command.foo_bar'.  The command class must provide a
    'user_options' attribute which is a list of option specifiers for
    'distutils2.fancy_getopt'.  Any command-line options between the current
    and the next command are used to set attributes of the current command
    object.

    When the entire command line has been successfully parsed, calls the
    'run()' method on each command object in turn.  This method will be
    driven entirely by the Distribution object (which each command object
    has a reference to, thanks to its constructor), and the
    command-specific options that became attributes of each command
    object.
    """
    # Determine the distribution class -- either caller-supplied or
    # our Distribution (see below).
    distclass = attrs.pop('distclass', Distribution)

    if 'script_name' not in attrs:
        attrs['script_name'] = os.path.basename(sys.argv[0])

    if 'script_args' not in attrs:
        if sys.argv[1] == "help":
            script_args = sys.argv[2:]
            script_args.append("--help")
        else:
            script_args = sys.argv[1:]
        attrs['script_args'] = script_args

    # Create the Distribution instance, using the remaining arguments
    # (ie. everything except distclass) to initialize it
    try:
        dist = distclass(attrs)
    except DistutilsSetupError, msg:
        if 'name' in attrs:
            raise SystemExit, "error in %s setup command: %s" % \
                  (attrs['name'], msg)
        else:
            raise SystemExit, "error in setup command: %s" % msg

    # Find and parse the config file(s): they will override options from
    # the setup script, but be overridden by the command line.
    dist.parse_config_files()

    # Parse the command line and override config files; any
    # command line errors are the end user's fault, so turn them into
    # SystemExit to suppress tracebacks.
    try:
        res = dist.parse_command_line()
    except DistutilsArgError, msg:
        raise SystemExit, gen_usage(dist.script_name) + "\nerror: %s" % msg

    # And finally, run all the commands found on the command line.
    if res:
        try:
            dist.run_commands()
        except KeyboardInterrupt:
            raise SystemExit, "interrupted"
        except (IOError, os.error), exc:
            error = grok_environment_error(exc)
            raise SystemExit, error

        except (DistutilsError,
                CCompilerError), msg:
            raise SystemExit, "error: " + str(msg)

    return dist


def _set_logger():
    logger.setLevel(logging.INFO)
    sth = logging.StreamHandler(sys.stderr)
    sth.setLevel(logging.INFO)
    logger.addHandler(sth)
    logger.propagate = 0


def main():
    """Main entry point for Distutils2"""
    _set_logger()
    parser = OptionParser()
    parser.disable_interspersed_args()
    parser.usage = '%prog [options] cmd1 cmd2 ..'

    parser.add_option("-v", "--version",
                  action="store_true", dest="version", default=False,
                  help="Prints out the version of Distutils2 and exits.")

    parser.add_option("-s", "--search",
                  action="store", dest="search", default=None,
                  help="Search for installed distributions.")

    parser.add_option("-g", "--graph",
                  action="store", dest="graph", default=None,
                  help="Display the graph for a given installed distribution.")

    parser.add_option("-f", "--full-graph",
                  action="store_true", dest="fgraph", default=False,
                  help="Display the full graph for installed distributions.")

    parser.add_option("-i", "--install",
                  action="store", dest="install",
                  help="Install a project.")

    options, args = parser.parse_args()
    if options.version:
        print('Distutils2 %s' % __version__)
        sys.exit(0)

    if options.search is not None:
        search = options.search.lower()
        for dist in get_distributions(use_egg_info=True):
            name = dist.name.lower()
            if search in name:
                print('%s %s at %s' % (dist.name, dist.metadata['version'],
                                     dist.path))

        sys.exit(0)

    if options.graph is not None:
        name = options.graph
        dist = get_distribution(name, use_egg_info=True)
        if dist is None:
            print('Distribution not found.')
        else:
            dists = get_distributions(use_egg_info=True)
            graph = generate_graph(dists)
            print(graph.repr_node(dist))

        sys.exit(0)

    if options.fgraph:
        dists = get_distributions(use_egg_info=True)
        graph = generate_graph(dists)
        print(graph)
        sys.exit(0)

    if options.install is not None:
        install(options.install)
        sys.exit(0)

    if len(args) == 0:
        parser.print_help()
        sys.exit(0)

    commands_main()
    sys.exit(0)


if __name__ == '__main__':
    main()
