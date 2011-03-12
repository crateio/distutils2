"""distutils2.dispatcher

Parses the command line.
"""
import logging
import re
import os
import sys

from distutils2.errors import DistutilsError, CCompilerError
from distutils2._backport.pkgutil import get_distributions, get_distribution
from distutils2.depgraph import generate_graph
from distutils2.install import install, remove
from distutils2.dist import Distribution

from distutils2.command import get_command_class, STANDARD_COMMANDS

from distutils2.errors import (DistutilsOptionError, DistutilsArgError,
                               DistutilsModuleError, DistutilsClassError)

from distutils2 import logger
from distutils2.fancy_getopt import FancyGetopt

command_re = re.compile(r'^[a-zA-Z]([a-zA-Z0-9_]*)$')

run_usage = """\
usage: pysetup run [global_opts] cmd1 [cmd1_opts] [cmd2 [cmd2_opts] ...]
   or: pysetup run --help
   or: pysetup run --list-commands
   or: pysetup run cmd --help
"""

common_usage = """\
Actions:
%(actions)s

To get more help on an action, use:

    pysetup action --help
"""

global_options = [('verbose', 'v', "run verbosely (default)", 1),
                  ('quiet', 'q', "run quietly (turns verbosity off)"),
                  ('dry-run', 'n', "don't actually do anything"),
                  ('help', 'h', "show detailed help message"),
                  ('no-user-cfg', None,
                   'ignore pydistutils.cfg in your home directory'),
                  ('version', None, 'Display the version'),
    ]

display_options = [
        ('help-commands', None,
         "list all available commands"),
        ]


display_option_names = [x[0].replace('-', '_') for x in display_options]
negative_opt = {'quiet': 'verbose'}

def _set_logger():
    logger.setLevel(logging.INFO)
    sth = logging.StreamHandler(sys.stderr)
    sth.setLevel(logging.INFO)
    logger.addHandler(sth)
    logger.propagate = 0

def _graph(dispatcher, args, **kw):
    # XXX
    dists = get_distributions(use_egg_info=True)
    graph = generate_graph(dists)
    print(graph)
    return 0


    name = args[0]
    dist = get_distribution(name, use_egg_info=True)
    if dist is None:
        print('Distribution not found.')
    else:
        dists = get_distributions(use_egg_info=True)
        graph = generate_graph(dists)
        print(graph.repr_node(dist))

    return 0



def _search(dispatcher, args, **kw):
    search = args[0].lower()
    for dist in get_distributions(use_egg_info=True):
        name = dist.name.lower()
        if search in name:
            print('%s %s at %s' % (dist.name, dist.metadata['version'],
                                    dist.path))

    return 0


def _metadata(dispatcher, args, **kw):
    ### XXX Needs to work on any installed package as well
    from distutils2.dist import Distribution
    dist = Distribution()
    dist.parse_config_files()
    metadata = dist.metadata

    if 'all' in args:
        keys = metadata.keys()
    else:
        keys = args
        if len(keys) == 1:
            print metadata[keys[0]]
            return

    for key in keys:
        if key in metadata:
            print(metadata._convert_name(key) + ':')
            value = metadata[key]
            if isinstance(value, list):
                for v in value:
                    print('    ' + v)
            else:
                print('    ' + value.replace('\n', '\n    '))
    return 0

def _run(dispatcher, args, **kw):
    parser = dispatcher.parser
    args = args[1:]

    commands = STANDARD_COMMANDS  # + extra commands

    # do we have a global option ?
    if args in (['--help'], []):
        print(run_usage)
        return

    if args == ['--list-commands']:
        print('List of available commands:')
        cmds = list(commands)
        cmds.sort()

        for cmd in cmds:
            cls = dispatcher.cmdclass.get(cmd) or get_command_class(cmd)
            desc = getattr(cls, 'description',
                            '(no description available)')
            print('  %s: %s' % (cmd, desc))
        return

    while args:
        args = dispatcher._parse_command_opts(parser, args)
        if args is None:
            return

    # create the Distribution class
    # need to feed setup.cfg here !
    dist = Distribution()

    # Find and parse the config file(s): they will override options from
    # the setup script, but be overridden by the command line.

    # XXX still need to be extracted from Distribution
    dist.parse_config_files()


    try:
        for cmd in dispatcher.commands:
            dist.run_command(cmd, dispatcher.command_options[cmd])

    except KeyboardInterrupt:
        raise SystemExit("interrupted")
    except (IOError, os.error, DistutilsError, CCompilerError), msg:
        raise SystemExit("error: " + str(msg))

    # XXX this is crappy
    return dist

def _install(dispatcher, args, **kw):
    install(args[0])
    return 0

def _remove(distpatcher, args, **kw):
    remove(options.remove)
    return 0

def _create(distpatcher, args, **kw):
    from distutils2.mkcfg import main
    main()
    return 0


actions = [('run', 'Run one or several commands', _run),
           ('metadata', 'Display the metadata of a project', _metadata),
           ('install', 'Install a project', _install),
           ('remove', 'Remove a project', _remove),
           ('search', 'Search for a project', _search),
           ('graph', 'Display a graph', _graph),
           ('create', 'Create a Project', _create),]




def fix_help_options(options):
    """Convert a 4-tuple 'help_options' list as found in various command
    classes to the 3-tuple form required by FancyGetopt.
    """
    new_options = []
    for help_tuple in options:
        new_options.append(help_tuple[0:3])
    return new_options



class Dispatcher(object):
    """Reads the command-line options
    """
    def __init__(self, args=None):
        self.verbose = 1
        self.dry_run = 0
        self.help = 0
        self.script_name = 'pysetup'
        self.cmdclass = {}
        self.commands = []
        self.command_options = {}

        for attr in display_option_names:
            setattr(self, attr, 0)

        self.parser = FancyGetopt(global_options + display_options)
        self.parser.set_negative_aliases(negative_opt)
        args = self.parser.getopt(args=args, object=self)

        #args = args[1:]

        # if first arg is "run", we have some commands
        if len(args) == 0:
            self.action = None
        else:
            self.action = args[0]

        allowed = [action[0] for action in actions] + [None]
        if self.action not in allowed:
            msg = 'Unrecognized action "%s"' % self.action
            raise DistutilsArgError(msg)

        # setting up the logger
        handler = logging.StreamHandler()
        logger.addHandler(handler)

        if self.verbose:
            handler.setLevel(logging.DEBUG)
        else:
            handler.setLevel(logging.INFO)

        # for display options we return immediately
        option_order = self.parser.get_option_order()

        self.args = args

        if self.help or self.action is None:
            self._show_help(self.parser, display_options_=False)
            return

    def _parse_command_opts(self, parser, args):
        # Pull the current command from the head of the command line
        command = args[0]
        if not command_re.match(command):
            raise SystemExit("invalid command name %r" % command)
        self.commands.append(command)

        # Dig up the command class that implements this command, so we
        # 1) know that it's a valid command, and 2) know which options
        # it takes.
        try:
            cmd_class = get_command_class(command)
        except DistutilsModuleError, msg:
            raise DistutilsArgError(msg)

        # XXX We want to push this in distutils.command
        #
        # Require that the command class be derived from Command -- want
        # to be sure that the basic "command" interface is implemented.
        for meth in ('initialize_options', 'finalize_options', 'run'):
            if hasattr(cmd_class, meth):
                continue
            raise DistutilsClassError(
                'command %r must implement %r' % (cmd_class, meth))

        # Also make sure that the command object provides a list of its
        # known options.
        if not (hasattr(cmd_class, 'user_options') and
                isinstance(cmd_class.user_options, list)):
            raise DistutilsClassError(
                "command class %s must provide "
                "'user_options' attribute (a list of tuples)" % cmd_class)

        # If the command class has a list of negative alias options,
        # merge it in with the global negative aliases.
        _negative_opt = negative_opt.copy()

        if hasattr(cmd_class, 'negative_opt'):
            _negative_opt.update(cmd_class.negative_opt)

        # Check for help_options in command class.  They have a different
        # format (tuple of four) so we need to preprocess them here.
        if (hasattr(cmd_class, 'help_options') and
            isinstance(cmd_class.help_options, list)):
            help_options = fix_help_options(cmd_class.help_options)
        else:
            help_options = []

        # All commands support the global options too, just by adding
        # in 'global_options'.
        parser.set_option_table(global_options +
                                cmd_class.user_options +
                                help_options)
        parser.set_negative_aliases(_negative_opt)
        args, opts = parser.getopt(args[1:])

        if hasattr(opts, 'help') and opts.help:
            self._show_command_help(cmd_class)
            return

        if (hasattr(cmd_class, 'help_options') and
            isinstance(cmd_class.help_options, list)):
            help_option_found = 0
            for (help_option, short, desc, func) in cmd_class.help_options:
                if hasattr(opts, help_option.replace('-', '_')):
                    help_option_found = 1
                    if hasattr(func, '__call__'):
                        func()
                    else:
                        raise DistutilsClassError(
                            "invalid help function %r for help option %r: "
                            "must be a callable object (function, etc.)"
                            % (func, help_option))

            if help_option_found:
                return

        # Put the options from the command line into their official
        # holding pen, the 'command_options' dictionary.
        opt_dict = self.get_option_dict(command)
        for (name, value) in vars(opts).iteritems():
            opt_dict[name] = ("command line", value)

        return args

    def get_option_dict(self, command):
        """Get the option dictionary for a given command.  If that
        command's option dictionary hasn't been created yet, then create it
        and return the new dictionary; otherwise, return the existing
        option dictionary.
        """
        d = self.command_options.get(command)
        if d is None:
            d = self.command_options[command] = {}
        return d

    def show_help(self):
        self._show_help(self.parser)

    def print_usage(self, parser):
        parser.set_option_table(global_options)

        actions_ = ['    %s: %s' % (name, desc) for name, desc, __ in actions]
        usage = common_usage % {'actions': '\n'.join(actions_)}

        parser.print_help(usage + "\nGlobal options:")

    def _show_help(self, parser, global_options_=1, display_options_=1,
                   commands=[]):
        # late import because of mutual dependence between these modules
        from distutils2.command.cmd import Command

        print('Usage: pysetup [options] action [action_options]')
        print('')
        if global_options_:
            self.print_usage(self.parser)
            print('')

        if display_options_:
            parser.set_option_table(display_options)
            parser.print_help(
                "Information display options (just display " +
                "information, ignore any commands)")
            print('')

        for command in commands:
            if isinstance(command, type) and issubclass(command, Command):
                cls = command
            else:
                cls = get_command_class(command)
            if (hasattr(cls, 'help_options') and
                isinstance(cls.help_options, list)):
                parser.set_option_table(cls.user_options +
                                        fix_help_options(cls.help_options))
            else:
                parser.set_option_table(cls.user_options)


            parser.print_help("Options for %r command:" % cls.__name__)
            print('')

    def _show_command_help(self, command):
        from distutils2.command.cmd import Command
        if isinstance(command, str):
            command = get_command_class(command)

        name = command.get_command_name()

        desc = getattr(command, 'description', '(no description available)')
        print('Description: %s' % desc)
        print('')

        if (hasattr(command, 'help_options') and
            isinstance(command.help_options, list)):
            self.parser.set_option_table(command.user_options +
                        fix_help_options(command.help_options))
        else:
            self.parser.set_option_table(command.user_options)

        self.parser.print_help("Options:")
        print('')

    def _get_command_groups(self):
        """Helper function to retrieve all the command class names divided
        into standard commands (listed in
        distutils2.command.STANDARD_COMMANDS) and extra commands (given in
        self.cmdclass and not standard commands).
        """
        extra_commands = [cmd for cmd in self.cmdclass
                          if cmd not in STANDARD_COMMANDS]
        return STANDARD_COMMANDS, extra_commands

    def print_commands(self):
        """Print out a help message listing all available commands with a
        description of each.  The list is divided into standard commands
        (listed in distutils2.command.STANDARD_COMMANDS) and extra commands
        (given in self.cmdclass and not standard commands).  The
        descriptions come from the command class attribute
        'description'.
        """
        std_commands, extra_commands = self._get_command_groups()
        max_length = 0
        for cmd in list(std_commands) + list(extra_commands):
            if len(cmd) > max_length:
                max_length = len(cmd)

        self.print_command_list(std_commands,
                                "Standard commands",
                                max_length)
        if extra_commands:
            print
            self.print_command_list(extra_commands,
                                    "Extra commands",
                                    max_length)


    def print_command_list(self, commands, header, max_length):
        """Print a subset of the list of all commands -- used by
        'print_commands()'.
        """
        print(header + ":")

        for cmd in commands:
            cls = self.cmdclass.get(cmd) or get_command_class(cmd)
            description = getattr(cls, 'description',
                                  '(no description available)')

            print("  %-*s  %s" % (max_length, cmd, description))


    def __call__(self):
        if self.action is None:
            return 0
        for action, desc, func in actions:
            if action == self.action:
                return func(self, self.args)
        return -1


def main(args=None):
    dispatcher = Dispatcher(args)
    if dispatcher.action is None:
        return 0

    return dispatcher()

if __name__ == '__main__':
    sys.exit(main())
