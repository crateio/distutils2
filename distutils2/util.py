"""Miscellaneous utility functions."""

import codecs
import os
import re
import csv
import sys
import errno
import shutil
import string
try:
    import hashlib
except ImportError: #<2.5
    from _backport import hashlib
import tarfile
import zipfile
import posixpath
import subprocess
import sysconfig
try:
    from glob import iglob as std_iglob
except ImportError:#<2.5
    from glob import glob as std_iglob
from fnmatch import fnmatchcase
from inspect import getsource
from ConfigParser import RawConfigParser

from distutils2 import logger
from distutils2.errors import (PackagingPlatformError, PackagingFileError,
                              PackagingByteCompileError, PackagingExecError,
                              InstallationException, PackagingInternalError)

_PLATFORM = None
_DEFAULT_INSTALLER = 'distutils2'


def newer(source, target):
    """Tell if the target is newer than the source.

    Returns true if 'source' exists and is more recently modified than
    'target', or if 'source' exists and 'target' doesn't.

    Returns false if both exist and 'target' is the same age or younger
    than 'source'. Raise PackagingFileError if 'source' does not exist.

    Note that this test is not very accurate: files created in the same second
    will have the same "age".
    """
    if not os.path.exists(source):
        raise PackagingFileError("file '%s' does not exist" %
                                 os.path.abspath(source))
    if not os.path.exists(target):
        return True

    return os.stat(source).st_mtime > os.stat(target).st_mtime


def get_platform():
    """Return a string that identifies the current platform.

    By default, will return the value returned by sysconfig.get_platform(),
    but it can be changed by calling set_platform().
    """
    global _PLATFORM
    if _PLATFORM is None:
        _PLATFORM = sysconfig.get_platform()
    return _PLATFORM


def set_platform(identifier):
    """Set the platform string identifier returned by get_platform().

    Note that this change doesn't impact the value returned by
    sysconfig.get_platform(); it is local to distutils2.
    """
    global _PLATFORM
    _PLATFORM = identifier


def convert_path(pathname):
    """Return 'pathname' as a name that will work on the native filesystem.

    The path is split on '/' and put back together again using the current
    directory separator.  Needed because filenames in the setup script are
    always supplied in Unix style, and have to be converted to the local
    convention before we can actually use them in the filesystem.  Raises
    ValueError on non-Unix-ish systems if 'pathname' either starts or
    ends with a slash.
    """
    if os.sep == '/':
        return pathname
    if not pathname:
        return pathname
    if pathname[0] == '/':
        raise ValueError("path '%s' cannot be absolute" % pathname)
    if pathname[-1] == '/':
        raise ValueError("path '%s' cannot end with '/'" % pathname)

    paths = pathname.split('/')
    while os.curdir in paths:
        paths.remove(os.curdir)
    if not paths:
        return os.curdir
    return os.path.join(*paths)


def change_root(new_root, pathname):
    """Return 'pathname' with 'new_root' prepended.

    If 'pathname' is relative, this is equivalent to
    os.path.join(new_root,pathname). Otherwise, it requires making 'pathname'
    relative and then joining the two, which is tricky on DOS/Windows.
    """
    if os.name == 'posix':
        if not os.path.isabs(pathname):
            return os.path.join(new_root, pathname)
        else:
            return os.path.join(new_root, pathname[1:])

    elif os.name == 'nt':
        drive, path = os.path.splitdrive(pathname)
        if path[0] == '\\':
            path = path[1:]
        return os.path.join(new_root, path)

    elif os.name == 'os2':
        drive, path = os.path.splitdrive(pathname)
        if path[0] == os.sep:
            path = path[1:]
        return os.path.join(new_root, path)

    else:
        raise PackagingPlatformError("nothing known about "
                                     "platform '%s'" % os.name)

_environ_checked = False


def check_environ():
    """Ensure that 'os.environ' has all the environment variables needed.

    We guarantee that users can use in config files, command-line options,
    etc.  Currently this includes:
      HOME - user's home directory (Unix only)
      PLAT - description of the current platform, including hardware
             and OS (see 'get_platform()')
    """
    global _environ_checked
    if _environ_checked:
        return

    if os.name == 'posix' and 'HOME' not in os.environ:
        import pwd
        os.environ['HOME'] = pwd.getpwuid(os.getuid())[5]

    if 'PLAT' not in os.environ:
        os.environ['PLAT'] = sysconfig.get_platform()

    _environ_checked = True


def subst_vars(s, local_vars):
    """Perform shell/Perl-style variable substitution on 'string'.

    Every occurrence of '$' followed by a name is considered a variable, and
    variable is substituted by the value found in the 'local_vars'
    dictionary, or in 'os.environ' if it's not in 'local_vars'.
    'os.environ' is first checked/augmented to guarantee that it contains
    certain values: see 'check_environ()'.  Raise ValueError for any
    variables not found in either 'local_vars' or 'os.environ'.
    """
    check_environ()

    def _subst(match, local_vars=local_vars):
        var_name = match.group(1)
        if var_name in local_vars:
            return str(local_vars[var_name])
        else:
            return os.environ[var_name]

    try:
        return re.sub(r'\$([a-zA-Z_][a-zA-Z_0-9]*)', _subst, s)
    except KeyError:
        raise ValueError("invalid variable '$%s'" % sys.exc_info()[1])


# Needed by 'split_quoted()'
_wordchars_re = _squote_re = _dquote_re = None


def _init_regex():
    global _wordchars_re, _squote_re, _dquote_re
    _wordchars_re = re.compile(r'[^\\\'\"%s ]*' % string.whitespace)
    _squote_re = re.compile(r"'(?:[^'\\]|\\.)*'")
    _dquote_re = re.compile(r'"(?:[^"\\]|\\.)*"')


def split_quoted(s):
    """Split a string up according to Unix shell-like rules for quotes and
    backslashes.

    In short: words are delimited by spaces, as long as those
    spaces are not escaped by a backslash, or inside a quoted string.
    Single and double quotes are equivalent, and the quote characters can
    be backslash-escaped.  The backslash is stripped from any two-character
    escape sequence, leaving only the escaped character.  The quote
    characters are stripped from any quoted string.  Returns a list of
    words.
    """
    # This is a nice algorithm for splitting up a single string, since it
    # doesn't require character-by-character examination.  It was a little
    # bit of a brain-bender to get it working right, though...
    if _wordchars_re is None:
        _init_regex()

    s = s.strip()
    words = []
    pos = 0

    while s:
        m = _wordchars_re.match(s, pos)
        end = m.end()
        if end == len(s):
            words.append(s[:end])
            break

        if s[end] in string.whitespace:  # unescaped, unquoted whitespace: now
            words.append(s[:end])        # we definitely have a word delimiter
            s = s[end:].lstrip()
            pos = 0

        elif s[end] == '\\':             # preserve whatever is being escaped;
                                         # will become part of the current word
            s = s[:end] + s[end + 1:]
            pos = end + 1

        else:
            if s[end] == "'":            # slurp singly-quoted string
                m = _squote_re.match(s, end)
            elif s[end] == '"':          # slurp doubly-quoted string
                m = _dquote_re.match(s, end)
            else:
                raise RuntimeError("this can't happen "
                                   "(bad char '%c')" % s[end])

            if m is None:
                raise ValueError("bad string (mismatched %s quotes?)" % s[end])

            beg, end = m.span()
            s = s[:beg] + s[beg + 1:end - 1] + s[end:]
            pos = m.end() - 2

        if pos >= len(s):
            words.append(s)
            break

    return words


def split_multiline(value):
    """Split a multiline string into a list, excluding blank lines."""

    return [element for element in
            (line.strip() for line in value.split('\n'))
            if element]


def execute(func, args, msg=None, verbose=0, dry_run=False):
    """Perform some action that affects the outside world.

    Some actions (e.g. writing to the filesystem) are special because
    they are disabled by the 'dry_run' flag.  This method takes care of all
    that bureaucracy for you; all you have to do is supply the
    function to call and an argument tuple for it (to embody the
    "external action" being performed), and an optional message to
    print.
    """
    if msg is None:
        msg = "%s%r" % (func.__name__, args)
        if msg[-2:] == ',)':        # correct for singleton tuple
            msg = msg[0:-2] + ')'

    logger.info(msg)
    if not dry_run:
        func(*args)


def strtobool(val):
    """Convert a string representation of truth to a boolean.

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))


def byte_compile(py_files, optimize=0, force=False, prefix=None,
                 base_dir=None, verbose=0, dry_run=False, direct=None):
    """Byte-compile a collection of Python source files to either .pyc
    or .pyo files in the same directory.

    'py_files' is a list of files to compile; any files that don't end in
    ".py" are silently skipped. 'optimize' must be one of the following:
      0 - don't optimize (generate .pyc)
      1 - normal optimization (like "python -O")
      2 - extra optimization (like "python -OO")
    If 'force' is true, all files are recompiled regardless of
    timestamps.

    The source filename encoded in each bytecode file defaults to the
    filenames listed in 'py_files'; you can modify these with 'prefix' and
    'basedir'.  'prefix' is a string that will be stripped off of each
    source filename, and 'base_dir' is a directory name that will be
    prepended (after 'prefix' is stripped).  You can supply either or both
    (or neither) of 'prefix' and 'base_dir', as you wish.

    If 'dry_run' is true, doesn't actually do anything that would
    affect the filesystem.

    Byte-compilation is either done directly in this interpreter process
    with the standard py_compile module, or indirectly by writing a
    temporary script and executing it.  Normally, you should let
    'byte_compile()' figure out to use direct compilation or not (see
    the source for details).  The 'direct' flag is used by the script
    generated in indirect mode; unless you know what you're doing, leave
    it set to None.
    """
    # nothing is done if sys.dont_write_bytecode is True
    # FIXME this should not raise an error
    if hasattr(sys, 'dont_write_bytecode') and sys.dont_write_bytecode:
        raise PackagingByteCompileError('byte-compiling is disabled.')

    # First, if the caller didn't force us into direct or indirect mode,
    # figure out which mode we should be in.  We take a conservative
    # approach: choose direct mode *only* if the current interpreter is
    # in debug mode and optimize is 0.  If we're not in debug mode (-O
    # or -OO), we don't know which level of optimization this
    # interpreter is running with, so we can't do direct
    # byte-compilation and be certain that it's the right thing.  Thus,
    # always compile indirectly if the current interpreter is in either
    # optimize mode, or if either optimization level was requested by
    # the caller.
    if direct is None:
        direct = (__debug__ and optimize == 0)

    # "Indirect" byte-compilation: write a temporary script and then
    # run it with the appropriate flags.
    if not direct:
        from tempfile import mkstemp
        # XXX script_fd may leak, use something better than mkstemp
        script_fd, script_name = mkstemp(".py")
        os.close(script_fd)
        script_fd = None
        logger.info("writing byte-compilation script '%s'", script_name)
        if not dry_run:
            if script_fd is not None:
                script = os.fdopen(script_fd, "w", encoding='utf-8')
            else:
                script = codecs.open(script_name, "w", encoding='utf-8')

            script.write("""\
from distutils2.util import byte_compile
files = [
""")

            # XXX would be nice to write absolute filenames, just for
            # safety's sake (script should be more robust in the face of
            # chdir'ing before running it).  But this requires abspath'ing
            # 'prefix' as well, and that breaks the hack in build_lib's
            # 'byte_compile()' method that carefully tacks on a trailing
            # slash (os.sep really) to make sure the prefix here is "just
            # right".  This whole prefix business is rather delicate -- the
            # problem is that it's really a directory, but I'm treating it
            # as a dumb string, so trailing slashes and so forth matter.

            #py_files = map(os.path.abspath, py_files)
            #if prefix:
            #    prefix = os.path.abspath(prefix)

            script.write(",\n".join(map(repr, py_files)) + "]\n")
            script.write("""
byte_compile(files, optimize=%r, force=%r,
             prefix=%r, base_dir=%r,
             verbose=%r, dry_run=False,
             direct=True)
""" % (optimize, force, prefix, base_dir, verbose))
        script.close()
        cmd = [sys.executable, script_name]
        if optimize == 1:
            cmd.insert(1, "-O")
        elif optimize == 2:
            cmd.insert(1, "-OO")

        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.pathsep.join(sys.path)
        try:
            spawn(cmd, env=env)
        finally:
            execute(os.remove, (script_name,), "removing %s" % script_name,
                    dry_run=dry_run)

    # "Direct" byte-compilation: use the py_compile module to compile
    # right here, right now.  Note that the script generated in indirect
    # mode simply calls 'byte_compile()' in direct mode, a weird sort of
    # cross-process recursion.  Hey, it works!
    else:
        from py_compile import compile

        for file in py_files:
            if file[-3:] != ".py":
                # This lets us be lazy and not filter filenames in
                # the "install_lib" command.
                continue

            # Terminology from the py_compile module:
            #   cfile - byte-compiled file
            #   dfile - purported source filename (same as 'file' by default)
            cfile = file + (__debug__ and "c" or "o")
            dfile = file
            if prefix:
                if file[:len(prefix)] != prefix:
                    raise ValueError("invalid prefix: filename %r doesn't "
                                     "start with %r" % (file, prefix))
                dfile = dfile[len(prefix):]
            if base_dir:
                dfile = os.path.join(base_dir, dfile)

            cfile_base = os.path.basename(cfile)
            if direct:
                if force or newer(file, cfile):
                    logger.info("byte-compiling %s to %s", file, cfile_base)
                    if not dry_run:
                        compile(file, cfile, dfile)
                else:
                    logger.debug("skipping byte-compilation of %s to %s",
                              file, cfile_base)


def rfc822_escape(header):
    """Return a form of *header* suitable for inclusion in an RFC 822-header.

    This function ensures there are 8 spaces after each newline.
    """
    lines = header.split('\n')
    sep = '\n' + 8 * ' '
    return sep.join(lines)

_RE_VERSION = re.compile('(\d+\.\d+(\.\d+)*)')
_MAC_OS_X_LD_VERSION = re.compile('^@\(#\)PROGRAM:ld  '
                                  'PROJECT:ld64-((\d+)(\.\d+)*)')


def _find_ld_version():
    """Find the ld version.  The version scheme differs under Mac OS X."""
    if sys.platform == 'darwin':
        return _find_exe_version('ld -v', _MAC_OS_X_LD_VERSION)
    else:
        return _find_exe_version('ld -v')


def _find_exe_version(cmd, pattern=_RE_VERSION):
    """Find the version of an executable by running `cmd` in the shell.

    `pattern` is a compiled regular expression.  If not provided, defaults
    to _RE_VERSION. If the command is not found, or the output does not
    match the mattern, returns None.
    """
    from subprocess import Popen, PIPE
    executable = cmd.split()[0]
    if find_executable(executable) is None:
        return None
    pipe = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    try:
        stdout, stderr = pipe.communicate()
    finally:
        pipe.stdout.close()
        pipe.stderr.close()
    # some commands like ld under MacOS X, will give the
    # output in the stderr, rather than stdout.
    if stdout != '':
        out_string = stdout
    else:
        out_string = stderr

    result = pattern.search(out_string)
    if result is None:
        return None
    return result.group(1)


def get_compiler_versions():
    """Return a tuple providing the versions of gcc, ld and dllwrap

    For each command, if a command is not found, None is returned.
    Otherwise a string with the version is returned.
    """
    gcc = _find_exe_version('gcc -dumpversion')
    ld = _find_ld_version()
    dllwrap = _find_exe_version('dllwrap --version')
    return gcc, ld, dllwrap


def newer_group(sources, target, missing='error'):
    """Return true if 'target' is out-of-date with respect to any file
    listed in 'sources'.

    In other words, if 'target' exists and is newer
    than every file in 'sources', return false; otherwise return true.
    'missing' controls what we do when a source file is missing; the
    default ("error") is to blow up with an OSError from inside 'stat()';
    if it is "ignore", we silently drop any missing source files; if it is
    "newer", any missing source files make us assume that 'target' is
    out-of-date (this is handy in "dry-run" mode: it'll make you pretend to
    carry out commands that wouldn't work because inputs are missing, but
    that doesn't matter because you're not actually going to run the
    commands).
    """
    # If the target doesn't even exist, then it's definitely out-of-date.
    if not os.path.exists(target):
        return True

    # Otherwise we have to find out the hard way: if *any* source file
    # is more recent than 'target', then 'target' is out-of-date and
    # we can immediately return true.  If we fall through to the end
    # of the loop, then 'target' is up-to-date and we return false.
    target_mtime = os.stat(target).st_mtime

    for source in sources:
        if not os.path.exists(source):
            if missing == 'error':      # blow up when we stat() the file
                pass
            elif missing == 'ignore':   # missing source dropped from
                continue                # target's dependency list
            elif missing == 'newer':    # missing source means target is
                return True             # out-of-date

        if os.stat(source).st_mtime > target_mtime:
            return True

    return False


def write_file(filename, contents):
    """Create *filename* and write *contents* to it.

    *contents* is a sequence of strings without line terminators.
    """
    f = open(filename, "w")
    for line in contents:
        f.write(line + "\n")
    f.close()

def _is_package(path):
    return os.path.isdir(path) and os.path.isfile(
        os.path.join(path, '__init__.py'))


# Code taken from the pip project
def _is_archive_file(name):
    archives = ('.zip', '.tar.gz', '.tar.bz2', '.tgz', '.tar')
    ext = splitext(name)[1].lower()
    return ext in archives


def _under(path, root):
    path = path.split(os.sep)
    root = root.split(os.sep)
    if len(root) > len(path):
        return False
    for pos, part in enumerate(root):
        if path[pos] != part:
            return False
    return True


def _package_name(root_path, path):
    # Return a dotted package name, given a subpath
    if not _under(path, root_path):
        raise ValueError('"%s" is not a subpath of "%s"' % (path, root_path))
    return path[len(root_path) + 1:].replace(os.sep, '.')


def find_packages(paths=(os.curdir,), exclude=()):
    """Return a list all Python packages found recursively within
    directories 'paths'

    'paths' should be supplied as a sequence of "cross-platform"
    (i.e. URL-style) path; it will be converted to the appropriate local
    path syntax.

    'exclude' is a sequence of package names to exclude; '*' can be used as
    a wildcard in the names, such that 'foo.*' will exclude all subpackages
    of 'foo' (but not 'foo' itself).
    """
    packages = []
    discarded = []

    def _discarded(path):
        for discard in discarded:
            if _under(path, discard):
                return True
        return False

    for path in paths:
        path = convert_path(path)
        for root, dirs, files in os.walk(path):
            for dir_ in dirs:
                fullpath = os.path.join(root, dir_)
                if _discarded(fullpath):
                    continue
                # we work only with Python packages
                if not _is_package(fullpath):
                    discarded.append(fullpath)
                    continue
                # see if it's excluded
                excluded = False
                package_name = _package_name(path, fullpath)
                for pattern in exclude:
                    if fnmatchcase(package_name, pattern):
                        excluded = True
                        break
                if excluded:
                    continue

                # adding it to the list
                packages.append(package_name)
    return packages


def resolve_name(name):
    """Resolve a name like ``module.object`` to an object and return it.

    Raise ImportError if the module or name is not found.
    """
    parts = name.split('.')
    cursor = len(parts)
    module_name = parts[:cursor]

    while cursor > 0:
        try:
            ret = __import__('.'.join(module_name))
            break
        except ImportError:
            if cursor == 0:
                raise
            cursor -= 1
            module_name = parts[:cursor]
            ret = ''

    for part in parts[1:]:
        try:
            ret = getattr(ret, part)
        except AttributeError:
            raise ImportError(sys.exc_info()[1])

    return ret


def splitext(path):
    """Like os.path.splitext, but take off .tar too"""
    base, ext = posixpath.splitext(path)
    if base.lower().endswith('.tar'):
        ext = base[-4:] + ext
        base = base[:-4]
    return base, ext


def unzip_file(filename, location, flatten=True):
    """Unzip the file *filename* into the *location* directory."""
    if not os.path.exists(location):
        os.makedirs(location)
    zipfp = open(filename, 'rb')

    zip = zipfile.ZipFile(zipfp)
    leading = has_leading_dir(zip.namelist()) and flatten
    for name in zip.namelist():
        data = zip.read(name)
        fn = name
        if leading:
            fn = split_leading_dir(name)[1]
        fn = os.path.join(location, fn)
        dir = os.path.dirname(fn)
        if not os.path.exists(dir):
            os.makedirs(dir)
        if fn.endswith('/') or fn.endswith('\\'):
            # A directory
            if not os.path.exists(fn):
                os.makedirs(fn)
        else:
            fp = open(fn, 'wb')
            fp.write(data)
            fp.close()
    zipfp.close()


def untar_file(filename, location):
    """Untar the file *filename* into the *location* directory."""
    if not os.path.exists(location):
        os.makedirs(location)
    if filename.lower().endswith('.gz') or filename.lower().endswith('.tgz'):
        mode = 'r:gz'
    elif (filename.lower().endswith('.bz2')
          or filename.lower().endswith('.tbz')):
        mode = 'r:bz2'
    elif filename.lower().endswith('.tar'):
        mode = 'r'
    else:
        mode = 'r:*'

    tar = tarfile.open(filename, mode)
    leading = has_leading_dir(member.name for member in tar.getmembers())
    for member in tar.getmembers():
        fn = member.name
        if leading:
            fn = split_leading_dir(fn)[1]
        path = os.path.join(location, fn)
        if member.isdir():
            if not os.path.exists(path):
                os.makedirs(path)
        else:
            try:
                fp = tar.extractfile(member)
            except (KeyError, AttributeError):
                # Some corrupt tar files seem to produce this
                # (specifically bad symlinks)
                continue
            try:
                if not os.path.exists(os.path.dirname(path)):
                    os.makedirs(os.path.dirname(path))
                    destfp = open(path, 'wb')
                    shutil.copyfileobj(fp, destfp)
                    destfp.close()
            except:
                fp.close()
                raise
            fp.close()

def has_leading_dir(paths):
    """Return true if all the paths have the same leading path name.

    In other words, check that everything is in one subdirectory in an
    archive.
    """
    common_prefix = None
    for path in paths:
        prefix, rest = split_leading_dir(path)
        if not prefix:
            return False
        elif common_prefix is None:
            common_prefix = prefix
        elif prefix != common_prefix:
            return False
    return True


def split_leading_dir(path):
    path = str(path)
    path = path.lstrip('/').lstrip('\\')
    if '/' in path and (('\\' in path and path.find('/') < path.find('\\'))
                        or '\\' not in path):
        return path.split('/', 1)
    elif '\\' in path:
        return path.split('\\', 1)
    else:
        return path, ''

if sys.platform == 'darwin':
    _cfg_target = None
    _cfg_target_split = None

def spawn(cmd, search_path=True, verbose=0, dry_run=False, env=None):
    """Run another program specified as a command list 'cmd' in a new process.

    'cmd' is just the argument list for the new process, ie.
    cmd[0] is the program to run and cmd[1:] are the rest of its arguments.
    There is no way to run a program with a name different from that of its
    executable.

    If 'search_path' is true (the default), the system's executable
    search path will be used to find the program; otherwise, cmd[0]
    must be the exact path to the executable.  If 'dry_run' is true,
    the command will not actually be run.

    If 'env' is given, it's a environment dictionary used for the execution
    environment.

    Raise PackagingExecError if running the program fails in any way; just
    return on success.
    """
    logger.debug('spawn: running %r', cmd)
    if dry_run:
        logger.debug('dry run, no process actually spawned')
        return
    if sys.platform == 'darwin':
        global _cfg_target, _cfg_target_split
        if _cfg_target is None:
            _cfg_target = sysconfig.get_config_var(
                                  'MACOSX_DEPLOYMENT_TARGET') or ''
            if _cfg_target:
                _cfg_target_split = [int(x) for x in _cfg_target.split('.')]
        if _cfg_target:
            # ensure that the deployment target of build process is not less
            # than that used when the interpreter was built. This ensures
            # extension modules are built with correct compatibility values
            env = env or os.environ
            cur_target = env.get('MACOSX_DEPLOYMENT_TARGET', _cfg_target)
            if _cfg_target_split > [int(x) for x in cur_target.split('.')]:
                my_msg = ('$MACOSX_DEPLOYMENT_TARGET mismatch: '
                          'now "%s" but "%s" during configure'
                                % (cur_target, _cfg_target))
                raise PackagingPlatformError(my_msg)
            env = dict(env, MACOSX_DEPLOYMENT_TARGET=cur_target)

    exit_status = subprocess.call(cmd, env=env)
    if exit_status != 0:
        msg = "command %r failed with exit status %d"
        raise PackagingExecError(msg % (cmd, exit_status))


def find_executable(executable, path=None):
    """Try to find 'executable' in the directories listed in 'path'.

    *path* is a string listing directories separated by 'os.pathsep' and
    defaults to os.environ['PATH'].  Returns the complete filename or None
    if not found.
    """
    if path is None:
        path = os.environ['PATH']
    paths = path.split(os.pathsep)
    base, ext = os.path.splitext(executable)

    if (sys.platform == 'win32' or os.name == 'os2') and (ext != '.exe'):
        executable = executable + '.exe'

    if not os.path.isfile(executable):
        for p in paths:
            f = os.path.join(p, executable)
            if os.path.isfile(f):
                # the file exists, we have a shot at spawn working
                return f
        return None
    else:
        return executable


DEFAULT_REPOSITORY = 'http://pypi.python.org/pypi'
DEFAULT_REALM = 'pypi'
DEFAULT_PYPIRC = """\
[distutils]
index-servers =
    pypi

[pypi]
username:%s
password:%s
"""


def get_pypirc_path():
    """Return path to pypirc config file."""
    return os.path.join(os.path.expanduser('~'), '.pypirc')


def generate_pypirc(username, password):
    """Create a default .pypirc file."""
    rc = get_pypirc_path()
    f = open(rc, 'w')
    f.write(DEFAULT_PYPIRC % (username, password))
    f.close()

    try:
        os.chmod(rc, 00600)
    except OSError:
        # should do something better here
        pass


def read_pypirc(repository=DEFAULT_REPOSITORY, realm=DEFAULT_REALM):
    """Read the .pypirc file."""
    rc = get_pypirc_path()
    if os.path.exists(rc):
        config = RawConfigParser()
        config.read(rc)
        sections = config.sections()
        if 'distutils' in sections:
            # let's get the list of servers
            index_servers = config.get('distutils', 'index-servers')
            _servers = [server.strip() for server in
                        index_servers.split('\n')
                        if server.strip() != '']
            if _servers == []:
                # nothing set, let's try to get the default pypi
                if 'pypi' in sections:
                    _servers = ['pypi']
                else:
                    # the file is not properly defined, returning
                    # an empty dict
                    return {}
            for server in _servers:
                current = {'server': server}
                current['username'] = config.get(server, 'username')

                # optional params
                for key, default in (('repository', DEFAULT_REPOSITORY),
                                     ('realm', DEFAULT_REALM),
                                     ('password', None)):
                    if config.has_option(server, key):
                        current[key] = config.get(server, key)
                    else:
                        current[key] = default
                if (current['server'] == repository or
                    current['repository'] == repository):
                    return current
        elif 'server-login' in sections:
            # old format
            server = 'server-login'
            if config.has_option(server, 'repository'):
                repository = config.get(server, 'repository')
            else:
                repository = DEFAULT_REPOSITORY

            return {'username': config.get(server, 'username'),
                    'password': config.get(server, 'password'),
                    'repository': repository,
                    'server': server,
                    'realm': DEFAULT_REALM}

    return {}


# utility functions for 2to3 support

def run_2to3(files, doctests_only=False, fixer_names=None,
             options=None, explicit=None):
    """ Wrapper function around the refactor() class which
    performs the conversions on a list of python files.
    Invoke 2to3 on a list of Python files. The files should all come
    from the build area, as the modification is done in-place."""

    #if not files:
    #    return

    # Make this class local, to delay import of 2to3
    from lib2to3.refactor import get_fixers_from_package, RefactoringTool
    fixers = []
    fixers = get_fixers_from_package('lib2to3.fixes')

    if fixer_names:
        for fixername in fixer_names:
            fixers.extend(fixer for fixer in
                          get_fixers_from_package(fixername))
    r = RefactoringTool(fixers, options=options)
    r.refactor(files, write=True, doctests_only=doctests_only)


class Mixin2to3(object):
    """ Wrapper class for commands that run 2to3.
    To configure 2to3, setup scripts may either change
    the class variables, or inherit from this class
    to override how 2to3 is invoked.
    """
    # provide list of fixers to run.
    # defaults to all from lib2to3.fixers
    fixer_names = None

    # options dictionary
    options = None

    # list of fixers to invoke even though they are marked as explicit
    explicit = None

    def run_2to3(self, files, doctests_only=False):
        """ Issues a call to util.run_2to3. """
        return run_2to3(files, doctests_only, self.fixer_names,
                        self.options, self.explicit)

RICH_GLOB = re.compile(r'\{([^}]*)\}')
_CHECK_RECURSIVE_GLOB = re.compile(r'[^/\\,{]\*\*|\*\*[^/\\,}]')
_CHECK_MISMATCH_SET = re.compile(r'^[^{]*\}|\{[^}]*$')


def iglob(path_glob):
    """Extended globbing function that supports ** and {opt1,opt2,opt3}."""
    if _CHECK_RECURSIVE_GLOB.search(path_glob):
        msg = """invalid glob %r: recursive glob "**" must be used alone"""
        raise ValueError(msg % path_glob)
    if _CHECK_MISMATCH_SET.search(path_glob):
        msg = """invalid glob %r: mismatching set marker '{' or '}'"""
        raise ValueError(msg % path_glob)
    return _iglob(path_glob)


def _iglob(path_glob):
    rich_path_glob = RICH_GLOB.split(path_glob, 1)
    if len(rich_path_glob) > 1:
        assert len(rich_path_glob) == 3, rich_path_glob
        prefix, set, suffix = rich_path_glob
        for item in set.split(','):
            for path in _iglob(''.join((prefix, item, suffix))):
                yield path
    else:
        if '**' not in path_glob:
            for item in std_iglob(path_glob):
                yield item
        else:
            prefix, radical = path_glob.split('**', 1)
            if prefix == '':
                prefix = '.'
            if radical == '':
                radical = '*'
            else:
                # we support both
                radical = radical.lstrip('/')
                radical = radical.lstrip('\\')
            for path, dir, files in os.walk(prefix):
                path = os.path.normpath(path)
                for file in _iglob(os.path.join(path, radical)):
                    yield file


def cfg_to_args(path='setup.cfg'):
    """Compatibility helper to use setup.cfg in setup.py.

    This functions uses an existing setup.cfg to generate a dictionnary of
    keywords that can be used by distutils.core.setup(**kwargs).  It is used
    by generate_setup_py.

    *file* is the path to the setup.cfg file.  If it doesn't exist,
    PackagingFileError is raised.
    """
    # We need to declare the following constants here so that it's easier to
    # generate the setup.py afterwards, using inspect.getsource.

    # XXX ** == needs testing
    D1_D2_SETUP_ARGS = {"name": ("metadata",),
                        "version": ("metadata",),
                        "author": ("metadata",),
                        "author_email": ("metadata",),
                        "maintainer": ("metadata",),
                        "maintainer_email": ("metadata",),
                        "url": ("metadata", "home_page"),
                        "description": ("metadata", "summary"),
                        "long_description": ("metadata", "description"),
                        "download-url": ("metadata",),
                        "classifiers": ("metadata", "classifier"),
                        "platforms": ("metadata", "platform"),  # **
                        "license": ("metadata",),
                        "requires": ("metadata", "requires_dist"),
                        "provides": ("metadata", "provides_dist"),  # **
                        "obsoletes": ("metadata", "obsoletes_dist"),  # **
                        "package_dir": ("files", 'packages_root'),
                        "packages": ("files",),
                        "scripts": ("files",),
                        "py_modules": ("files", "modules"),  # **
                        }

    MULTI_FIELDS = ("classifiers",
                    "platforms",
                    "requires",
                    "provides",
                    "obsoletes",
                    "packages",
                    "scripts",
                    "py_modules")

    def has_get_option(config, section, option):
        if config.has_option(section, option):
            return config.get(section, option)
        elif config.has_option(section, option.replace('_', '-')):
            return config.get(section, option.replace('_', '-'))
        else:
            return False

    # The real code starts here
    config = RawConfigParser()
    if not os.path.exists(path):
        raise PackagingFileError("file '%s' does not exist" %
                                 os.path.abspath(path))
    f = codecs.open(path, encoding='utf-8')
    config.readfp(f)
    f.close()

    kwargs = {}
    for arg in D1_D2_SETUP_ARGS:
        if len(D1_D2_SETUP_ARGS[arg]) == 2:
            # The distutils field name is different than distutils2's
            section, option = D1_D2_SETUP_ARGS[arg]

        else:
            # The distutils field name is the same thant distutils2's
            section = D1_D2_SETUP_ARGS[arg][0]
            option = arg

        in_cfg_value = has_get_option(config, section, option)
        if not in_cfg_value:
            # There is no such option in the setup.cfg
            if arg == 'long_description':
                filenames = has_get_option(config, section, 'description-file')
                if filenames:
                    filenames = split_multiline(filenames)
                    in_cfg_value = []
                    for filename in filenames:
                        fp = open(filename)
                        in_cfg_value.append(fp.read())
                        fp.close()
                    in_cfg_value = '\n\n'.join(in_cfg_value)
            else:
                continue

        if arg == 'package_dir' and in_cfg_value:
            in_cfg_value = {'': in_cfg_value}

        if arg in MULTI_FIELDS:
            # support multiline options
            in_cfg_value = split_multiline(in_cfg_value)

        kwargs[arg] = in_cfg_value

    return kwargs


_SETUP_TMPL = """\
# This script was automatically generated by distutils2
import os
from distutils.core import setup
from ConfigParser import RawConfigParser

%(func)s

setup(**cfg_to_args())
"""


def generate_setup_py():
    """Generate a distutils compatible setup.py using an existing setup.cfg.

    Raises a PackagingFileError when a setup.py already exists.
    """
    if os.path.exists("setup.py"):
        raise PackagingFileError("a setup.py file already exists")

    fp = codecs.open("setup.py", "w", encoding='utf-8')
    fp.write(_SETUP_TMPL % {'func': getsource(cfg_to_args)})
    fp.close()


# Taken from the pip project
# https://github.com/pypa/pip/blob/master/pip/util.py
def ask(message, options):
    """Prompt the user with *message*; *options* contains allowed responses."""
    while True:
        response = raw_input(message)
        response = response.strip().lower()
        if response not in options:
            print 'invalid response:', repr(response)
            print 'choose one of', ', '.join(repr(o) for o in options)
        else:
            return response


def _parse_record_file(record_file):
    distinfo, extra_metadata, installed = ({}, [], [])
    rfile = open(record_file, 'r')
    for path in rfile:
        path = path.strip()
        if path.endswith('egg-info') and os.path.isfile(path):
            distinfo_dir = path.replace('egg-info', 'dist-info')
            metadata = path
            egginfo = path
        elif path.endswith('egg-info') and os.path.isdir(path):
            distinfo_dir = path.replace('egg-info', 'dist-info')
            egginfo = path
            for metadata_file in os.listdir(path):
                metadata_fpath = os.path.join(path, metadata_file)
                if metadata_file == 'PKG-INFO':
                    metadata = metadata_fpath
                else:
                    extra_metadata.append(metadata_fpath)
        elif 'egg-info' in path and os.path.isfile(path):
            # skip extra metadata files
            continue
        else:
            installed.append(path)

    distinfo['egginfo'] = egginfo
    distinfo['metadata'] = metadata
    distinfo['distinfo_dir'] = distinfo_dir
    distinfo['installer_path'] = os.path.join(distinfo_dir, 'INSTALLER')
    distinfo['metadata_path'] = os.path.join(distinfo_dir, 'METADATA')
    distinfo['record_path'] = os.path.join(distinfo_dir, 'RECORD')
    distinfo['requested_path'] = os.path.join(distinfo_dir, 'REQUESTED')
    installed.extend([distinfo['installer_path'], distinfo['metadata_path']])
    distinfo['installed'] = installed
    distinfo['extra_metadata'] = extra_metadata
    return distinfo


def _write_record_file(record_path, installed_files):
    f = codecs.open(record_path, 'w', encoding='utf-8')
    writer = csv.writer(f, delimiter=',', lineterminator=os.linesep,
                        quotechar='"')

    for fpath in installed_files:
        if fpath.endswith('.pyc') or fpath.endswith('.pyo'):
            # do not put size and md5 hash, as in PEP-376
            writer.writerow((fpath, '', ''))
        else:
            hash = hashlib.md5()
            fp = open(fpath, 'rb')
            hash.update(fp.read())
            fp.close()
            md5sum = hash.hexdigest()
            size = os.path.getsize(fpath)
            writer.writerow((fpath, md5sum, size))

    # add the RECORD file itself
    writer.writerow((record_path, '', ''))
    f.close()
    return record_path


def egginfo_to_distinfo(record_file, installer=_DEFAULT_INSTALLER,
                        requested=False, remove_egginfo=False):
    """Create files and directories required for PEP 376

    :param record_file: path to RECORD file as produced by setup.py --record
    :param installer: installer name
    :param requested: True if not installed as a dependency
    :param remove_egginfo: delete egginfo dir?
    """
    distinfo = _parse_record_file(record_file)
    distinfo_dir = distinfo['distinfo_dir']
    if os.path.isdir(distinfo_dir) and not os.path.islink(distinfo_dir):
        shutil.rmtree(distinfo_dir)
    elif os.path.exists(distinfo_dir):
        os.unlink(distinfo_dir)

    os.makedirs(distinfo_dir)

    # copy setuptools extra metadata files
    if distinfo['extra_metadata']:
        for path in distinfo['extra_metadata']:
            shutil.copy2(path, distinfo_dir)
            new_path = path.replace('egg-info', 'dist-info')
            distinfo['installed'].append(new_path)

    metadata_path = distinfo['metadata_path']
    logger.info('creating %s', metadata_path)
    shutil.copy2(distinfo['metadata'], metadata_path)

    installer_path = distinfo['installer_path']
    logger.info('creating %s', installer_path)
    f = open(installer_path, 'w')
    f.write(installer)
    f.close()

    if requested:
        requested_path = distinfo['requested_path']
        logger.info('creating %s', requested_path)
        open(requested_path, 'wb').close()
        distinfo['installed'].append(requested_path)

    record_path = distinfo['record_path']
    logger.info('creating %s', record_path)
    _write_record_file(record_path, distinfo['installed'])

    if remove_egginfo:
        egginfo = distinfo['egginfo']
        logger.info('removing %s', egginfo)
        if os.path.isfile(egginfo):
            os.remove(egginfo)
        else:
            shutil.rmtree(egginfo)


def _has_egg_info(srcdir):
    if os.path.isdir(srcdir):
        for item in os.listdir(srcdir):
            full_path = os.path.join(srcdir, item)
            if item.endswith('.egg-info') and os.path.isdir(full_path):
                logger.debug("Found egg-info directory.")
                return True
    logger.debug("No egg-info directory found.")
    return False


def _has_setuptools_text(setup_py):
    return _has_text(setup_py, 'setuptools')


def _has_distutils_text(setup_py):
    return _has_text(setup_py, 'distutils')


def _has_text(setup_py, installer):
    installer_pattern = re.compile('import %s|from %s' % (
        installer[0], installer[1]))
    setup = codecs.open(setup_py, 'r', encoding='utf-8')
    for line in setup:
        if re.search(installer_pattern, line):
            logger.debug("Found %s text in setup.py.", installer)
            return True
    setup.close()
    logger.debug("No %s text found in setup.py.", installer)
    return False


def _has_required_metadata(setup_cfg):
    config = RawConfigParser()
    f = codecs.open(setup_cfg, 'r', encoding='utf8')
    config.readfp(f)
    f.close()
    return (config.has_section('metadata') and
            'name' in config.options('metadata') and
            'version' in config.options('metadata'))


def _has_pkg_info(srcdir):
    pkg_info = os.path.join(srcdir, 'PKG-INFO')
    has_pkg_info = os.path.isfile(pkg_info)
    if has_pkg_info:
        logger.debug("PKG-INFO file found.")
    else:
        logger.debug("No PKG-INFO file found.")
    return has_pkg_info


def _has_setup_py(srcdir):
    setup_py = os.path.join(srcdir, 'setup.py')
    if os.path.isfile(setup_py):
        logger.debug('setup.py file found.')
        return True
    return False


def _has_setup_cfg(srcdir):
    setup_cfg = os.path.join(srcdir, 'setup.cfg')
    if os.path.isfile(setup_cfg):
        logger.debug('setup.cfg file found.')
        return True
    logger.debug("No setup.cfg file found.")
    return False


def is_setuptools(path):
    """Check if the project is based on setuptools.

    :param path: path to source directory containing a setup.py script.

    Return True if the project requires setuptools to install, else False.
    """
    srcdir = os.path.abspath(path)
    setup_py = os.path.join(srcdir, 'setup.py')

    return _has_setup_py(srcdir) and (_has_egg_info(srcdir) or
                                      _has_setuptools_text(setup_py))


def is_distutils(path):
    """Check if the project is based on distutils.

    :param path: path to source directory containing a setup.py script.

    Return True if the project requires distutils to install, else False.
    """
    srcdir = os.path.abspath(path)
    setup_py = os.path.join(srcdir, 'setup.py')

    return _has_setup_py(srcdir) and (_has_pkg_info(srcdir) or
                                      _has_distutils_text(setup_py))


def is_distutils2(path):
    """Check if the project is based on distutils2

    :param path: path to source directory containing a setup.cfg file.

    Return True if the project has a valid setup.cfg, else False.
    """
    srcdir = os.path.abspath(path)
    setup_cfg = os.path.join(srcdir, 'setup.cfg')

    return _has_setup_cfg(srcdir) and _has_required_metadata(setup_cfg)


def get_install_method(path):
    """Check if the project is based on distutils2, setuptools, or distutils

    :param path: path to source directory containing a setup.cfg file,
                 or setup.py.

    Returns a string representing the best install method to use.
    """
    if is_distutils2(path):
        return "distutils2"
    elif is_setuptools(path):
        return "setuptools"
    elif is_distutils(path):
        return "distutils"
    else:
        raise InstallationException('Cannot detect install method')


# XXX to be replaced by shutil.copytree
def copy_tree(src, dst, preserve_mode=True, preserve_times=True,
              preserve_symlinks=False, update=False, verbose=True,
              dry_run=False):
    from distutils.file_util import copy_file

    if not dry_run and not os.path.isdir(src):
        raise PackagingFileError(
              "cannot copy tree '%s': not a directory" % src)
    try:
        names = os.listdir(src)
    except os.error:
        errstr = sys.exc_info()[1][1]
        if dry_run:
            names = []
        else:
            raise PackagingFileError(
                  "error listing files in '%s': %s" % (src, errstr))

    if not dry_run:
        _mkpath(dst, verbose=verbose)

    outputs = []

    for n in names:
        src_name = os.path.join(src, n)
        dst_name = os.path.join(dst, n)

        if preserve_symlinks and os.path.islink(src_name):
            link_dest = os.readlink(src_name)
            if verbose >= 1:
                logger.info("linking %s -> %s", dst_name, link_dest)
            if not dry_run:
                os.symlink(link_dest, dst_name)
            outputs.append(dst_name)

        elif os.path.isdir(src_name):
            outputs.extend(
                copy_tree(src_name, dst_name, preserve_mode,
                          preserve_times, preserve_symlinks, update,
                          verbose=verbose, dry_run=dry_run))
        else:
            copy_file(src_name, dst_name, preserve_mode,
                      preserve_times, update, verbose=verbose,
                      dry_run=dry_run)
            outputs.append(dst_name)

    return outputs

# cache for by mkpath() -- in addition to cheapening redundant calls,
# eliminates redundant "creating /foo/bar/baz" messages in dry-run mode
_path_created = set()


# I don't use os.makedirs because a) it's new to Python 1.5.2, and
# b) it blows up if the directory already exists (I want to silently
# succeed in that case).
def _mkpath(name, mode=00777, verbose=True, dry_run=False):
    # Detect a common bug -- name is None
    if not isinstance(name, basestring):
        raise PackagingInternalError(
              "mkpath: 'name' must be a string (got %r)" % (name,))

    # XXX what's the better way to handle verbosity? print as we create
    # each directory in the path (the current behaviour), or only announce
    # the creation of the whole path? (quite easy to do the latter since
    # we're not using a recursive algorithm)

    name = os.path.normpath(name)
    created_dirs = []
    if os.path.isdir(name) or name == '':
        return created_dirs
    if os.path.abspath(name) in _path_created:
        return created_dirs

    head, tail = os.path.split(name)
    tails = [tail]                      # stack of lone dirs to create

    while head and tail and not os.path.isdir(head):
        head, tail = os.path.split(head)
        tails.insert(0, tail)          # push next higher dir onto stack

    # now 'head' contains the deepest directory that already exists
    # (that is, the child of 'head' in 'name' is the highest directory
    # that does *not* exist)
    for d in tails:
        head = os.path.join(head, d)
        abs_head = os.path.abspath(head)

        if abs_head in _path_created:
            continue

        if verbose >= 1:
            logger.info("creating %s", head)

        if not dry_run:
            try:
                os.mkdir(head, mode)
            except OSError:
                exc = sys.exc_info()[1]
                if not (exc.errno == errno.EEXIST and os.path.isdir(head)):
                    raise PackagingFileError(
                          "could not create '%s': %s" % (head, exc.args[-1]))
            created_dirs.append(head)

        _path_created.add(abs_head)
    return created_dirs


def encode_multipart(fields, files, boundary=None):
    """Prepare a multipart HTTP request.

    *fields* is a sequence of (name: str, value: str) elements for regular
    form fields, *files* is a sequence of (name: str, filename: str, value:
    bytes) elements for data to be uploaded as files.

    Returns (content_type: bytes, body: bytes) ready for httplib.HTTP.
    """
    # Taken from
    # http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/

    if boundary is None:
        boundary = '--------------GHSKFJDLGDS7543FJKLFHRE75642756743254'
    elif not isinstance(boundary, str):
        raise TypeError('boundary must be str, not %r' % type(boundary))

    l = []
    for key, values in fields:
        # handle multiple entries for the same name
        if not isinstance(values, (tuple, list)):
            values=[values]

        for value in values:
            l.extend((
                '--' + boundary,
                ('Content-Disposition: form-data; name="%s"' % key), '', value))

    for key, filename, value in files:
        l.extend((
            '--' + boundary,
            ('Content-Disposition: form-data; name="%s"; filename="%s"' %
             (key, filename)),
            '',
            value))

    l.append('--' + boundary + '--')
    l.append('')

    body = '\r\n'.join(l)
    content_type = 'multipart/form-data; boundary=' + boundary
    return content_type, body

# shutil stuff

try:
    import bz2
    _BZ2_SUPPORTED = True
except ImportError:
    _BZ2_SUPPORTED = False

try:
    from pwd import getpwnam
except ImportError:
    getpwnam = None

try:
    from grp import getgrnam
except ImportError:
    getgrnam = None

def _get_gid(name):
    """Returns a gid, given a group name."""
    if getgrnam is None or name is None:
        return None
    try:
        result = getgrnam(name)
    except KeyError:
        result = None
    if result is not None:
        return result[2]
    return None

def _get_uid(name):
    """Returns an uid, given a user name."""
    if getpwnam is None or name is None:
        return None
    try:
        result = getpwnam(name)
    except KeyError:
        result = None
    if result is not None:
        return result[2]
    return None

def _make_tarball(base_name, base_dir, compress="gzip", verbose=0, dry_run=0,
                  owner=None, group=None, logger=None):
    """Create a (possibly compressed) tar file from all the files under
    'base_dir'.

    'compress' must be "gzip" (the default), "bzip2", or None.

    'owner' and 'group' can be used to define an owner and a group for the
    archive that is being built. If not provided, the current owner and group
    will be used.

    The output tar file will be named 'base_name' +  ".tar", possibly plus
    the appropriate compression extension (".gz", or ".bz2").

    Returns the output filename.
    """
    tar_compression = {'gzip': 'gz', None: ''}
    compress_ext = {'gzip': '.gz'}

    if _BZ2_SUPPORTED:
        tar_compression['bzip2'] = 'bz2'
        compress_ext['bzip2'] = '.bz2'

    # flags for compression program, each element of list will be an argument
    if compress is not None and compress not in compress_ext.keys():
        raise ValueError("bad value for 'compress', or compression format not "
                         "supported : %s" % compress)

    archive_name = base_name + '.tar' + compress_ext.get(compress, '')
    archive_dir = os.path.dirname(archive_name)

    if not os.path.exists(archive_dir):
        if logger is not None:
            logger.info("creating %s" % archive_dir)
        if not dry_run:
            os.makedirs(archive_dir)

    # creating the tarball
    if logger is not None:
        logger.info('Creating tar archive')

    uid = _get_uid(owner)
    gid = _get_gid(group)

    def _set_uid_gid(tarinfo):
        if gid is not None:
            tarinfo.gid = gid
            tarinfo.gname = group
        if uid is not None:
            tarinfo.uid = uid
            tarinfo.uname = owner
        return tarinfo

    if not dry_run:
        tar = tarfile.open(archive_name, 'w|%s' % tar_compression[compress])
        try:
            #tar.add(base_dir, filter=_set_uid_gid)
            tar.add(base_dir)
        finally:
            tar.close()

    return archive_name

def _call_external_zip(base_dir, zip_filename, verbose=False, dry_run=False):
    # XXX see if we want to keep an external call here
    if verbose:
        zipoptions = "-r"
    else:
        zipoptions = "-rq"
    from distutils.errors import DistutilsExecError
    from distutils.spawn import spawn
    try:
        spawn(["zip", zipoptions, zip_filename, base_dir], dry_run=dry_run)
    except DistutilsExecError:
        # XXX really should distinguish between "couldn't find
        # external 'zip' command" and "zip failed".
        raise ExecError("unable to create zip file '%s': "
            "could neither import the 'zipfile' module nor "
            "find a standalone zip utility") % zip_filename

def _make_zipfile(base_name, base_dir, verbose=0, dry_run=0, logger=None):
    """Create a zip file from all the files under 'base_dir'.

    The output zip file will be named 'base_name' + ".zip".  Uses either the
    "zipfile" Python module (if available) or the InfoZIP "zip" utility
    (if installed and found on the default search path).  If neither tool is
    available, raises ExecError.  Returns the name of the output zip
    file.
    """
    zip_filename = base_name + ".zip"
    archive_dir = os.path.dirname(base_name)

    if not os.path.exists(archive_dir):
        if logger is not None:
            logger.info("creating %s", archive_dir)
        if not dry_run:
            os.makedirs(archive_dir)

    # If zipfile module is not available, try spawning an external 'zip'
    # command.
    try:
        import zipfile
    except ImportError:
        zipfile = None

    if zipfile is None:
        _call_external_zip(base_dir, zip_filename, verbose, dry_run)
    else:
        if logger is not None:
            logger.info("creating '%s' and adding '%s' to it",
                        zip_filename, base_dir)

        if not dry_run:
            zip = zipfile.ZipFile(zip_filename, "w",
                                  compression=zipfile.ZIP_DEFLATED)

            for dirpath, dirnames, filenames in os.walk(base_dir):
                for name in filenames:
                    path = os.path.normpath(os.path.join(dirpath, name))
                    if os.path.isfile(path):
                        zip.write(path, path)
                        if logger is not None:
                            logger.info("adding '%s'", path)
            zip.close()

    return zip_filename

_ARCHIVE_FORMATS = {
    'gztar': (_make_tarball, [('compress', 'gzip')], "gzip'ed tar-file"),
    'bztar': (_make_tarball, [('compress', 'bzip2')], "bzip2'ed tar-file"),
    'tar':   (_make_tarball, [('compress', None)], "uncompressed tar file"),
    'zip':   (_make_zipfile, [],"ZIP file")
    }

if _BZ2_SUPPORTED:
    _ARCHIVE_FORMATS['bztar'] = (_make_tarball, [('compress', 'bzip2')],
                                "bzip2'ed tar-file")

def get_archive_formats():
    """Returns a list of supported formats for archiving and unarchiving.

    Each element of the returned sequence is a tuple (name, description)
    """
    formats = [(name, registry[2]) for name, registry in
               _ARCHIVE_FORMATS.items()]
    formats.sort()
    return formats

def register_archive_format(name, function, extra_args=None, description=''):
    """Registers an archive format.

    name is the name of the format. function is the callable that will be
    used to create archives. If provided, extra_args is a sequence of
    (name, value) tuples that will be passed as arguments to the callable.
    description can be provided to describe the format, and will be returned
    by the get_archive_formats() function.
    """
    if extra_args is None:
        extra_args = []
    if not isinstance(function, collections.Callable):
        raise TypeError('The %s object is not callable' % function)
    if not isinstance(extra_args, (tuple, list)):
        raise TypeError('extra_args needs to be a sequence')
    for element in extra_args:
        if not isinstance(element, (tuple, list)) or len(element) !=2 :
            raise TypeError('extra_args elements are : (arg_name, value)')

    _ARCHIVE_FORMATS[name] = (function, extra_args, description)

def unregister_archive_format(name):
    del _ARCHIVE_FORMATS[name]

def make_archive(base_name, format, root_dir=None, base_dir=None, verbose=0,
                 dry_run=0, owner=None, group=None, logger=None):
    """Create an archive file (eg. zip or tar).

    'base_name' is the name of the file to create, minus any format-specific
    extension; 'format' is the archive format: one of "zip", "tar", "bztar"
    or "gztar".

    'root_dir' is a directory that will be the root directory of the
    archive; ie. we typically chdir into 'root_dir' before creating the
    archive.  'base_dir' is the directory where we start archiving from;
    ie. 'base_dir' will be the common prefix of all files and
    directories in the archive.  'root_dir' and 'base_dir' both default
    to the current directory.  Returns the name of the archive file.

    'owner' and 'group' are used when creating a tar archive. By default,
    uses the current owner and group.
    """
    save_cwd = os.getcwd()
    base_name = fsencode(base_name)
    if root_dir is not None:
        if logger is not None:
            logger.debug("changing into '%s'", root_dir)
        base_name = os.path.abspath(base_name)
        if not dry_run:
            os.chdir(root_dir)

    if base_dir is None:
        base_dir = os.curdir

    kwargs = {'dry_run': dry_run, 'logger': logger}

    try:
        format_info = _ARCHIVE_FORMATS[format]
    except KeyError:
        raise ValueError("unknown archive format '%s'" % format)

    func = format_info[0]
    for arg, val in format_info[1]:
        kwargs[arg] = val

    if format != 'zip':
        kwargs['owner'] = owner
        kwargs['group'] = group

    try:
        filename = func(base_name, base_dir, **kwargs)
    finally:
        if root_dir is not None:
            if logger is not None:
                logger.debug("changing back to '%s'", save_cwd)
            os.chdir(save_cwd)

    return filename


def get_unpack_formats():
    """Returns a list of supported formats for unpacking.

    Each element of the returned sequence is a tuple
    (name, extensions, description)
    """
    formats = [(name, info[0], info[3]) for name, info in
               _UNPACK_FORMATS.items()]
    formats.sort()
    return formats

def _check_unpack_options(extensions, function, extra_args):
    """Checks what gets registered as an unpacker."""
    # first make sure no other unpacker is registered for this extension
    existing_extensions = {}
    for name, info in _UNPACK_FORMATS.items():
        for ext in info[0]:
            existing_extensions[ext] = name

    for extension in extensions:
        if extension in existing_extensions:
            msg = '%s is already registered for "%s"'
            raise RegistryError(msg % (extension,
                                       existing_extensions[extension]))

    if not isinstance(function, collections.Callable):
        raise TypeError('The registered function must be a callable')


def register_unpack_format(name, extensions, function, extra_args=None,
                           description=''):
    """Registers an unpack format.

    `name` is the name of the format. `extensions` is a list of extensions
    corresponding to the format.

    `function` is the callable that will be
    used to unpack archives. The callable will receive archives to unpack.
    If it's unable to handle an archive, it needs to raise a ReadError
    exception.

    If provided, `extra_args` is a sequence of
    (name, value) tuples that will be passed as arguments to the callable.
    description can be provided to describe the format, and will be returned
    by the get_unpack_formats() function.
    """
    if extra_args is None:
        extra_args = []
    _check_unpack_options(extensions, function, extra_args)
    _UNPACK_FORMATS[name] = extensions, function, extra_args, description

def unregister_unpack_format(name):
    """Removes the pack format from the registery."""
    del _UNPACK_FORMATS[name]

def _ensure_directory(path):
    """Ensure that the parent directory of `path` exists"""
    dirname = os.path.dirname(path)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

def _unpack_zipfile(filename, extract_dir):
    """Unpack zip `filename` to `extract_dir`
    """
    try:
        import zipfile
    except ImportError:
        raise ReadError('zlib not supported, cannot unpack this archive.')

    if not zipfile.is_zipfile(filename):
        raise ReadError("%s is not a zip file" % filename)

    zip = zipfile.ZipFile(filename)
    try:
        for info in zip.infolist():
            name = info.filename

            # don't extract absolute paths or ones with .. in them
            if name.startswith('/') or '..' in name:
                continue

            target = os.path.join(extract_dir, *name.split('/'))
            if not target:
                continue

            _ensure_directory(target)
            if not name.endswith('/'):
                # file
                data = zip.read(info.filename)
                f = open(target,'wb')
                try:
                    f.write(data)
                finally:
                    f.close()
                    del data
    finally:
        zip.close()

def _unpack_tarfile(filename, extract_dir):
    """Unpack tar/tar.gz/tar.bz2 `filename` to `extract_dir`
    """
    try:
        tarobj = tarfile.open(filename)
    except tarfile.TarError:
        raise ReadError(
            "%s is not a compressed or uncompressed tar file" % filename)
    try:
        tarobj.extractall(extract_dir)
    finally:
        tarobj.close()

_UNPACK_FORMATS = {
    'gztar': (['.tar.gz', '.tgz'], _unpack_tarfile, [], "gzip'ed tar-file"),
    'tar':   (['.tar'], _unpack_tarfile, [], "uncompressed tar file"),
    'zip':   (['.zip'], _unpack_zipfile, [], "ZIP file")
    }

if _BZ2_SUPPORTED:
    _UNPACK_FORMATS['bztar'] = (['.bz2'], _unpack_tarfile, [],
                                "bzip2'ed tar-file")

def _find_unpack_format(filename):
    for name, info in _UNPACK_FORMATS.items():
        for extension in info[0]:
            if filename.endswith(extension):
                return name
    return None

def unpack_archive(filename, extract_dir=None, format=None):
    """Unpack an archive.

    `filename` is the name of the archive.

    `extract_dir` is the name of the target directory, where the archive
    is unpacked. If not provided, the current working directory is used.

    `format` is the archive format: one of "zip", "tar", or "gztar". Or any
    other registered format. If not provided, unpack_archive will use the
    filename extension and see if an unpacker was registered for that
    extension.

    In case none is found, a ValueError is raised.
    """
    if extract_dir is None:
        extract_dir = os.getcwd()

    if format is not None:
        try:
            format_info = _UNPACK_FORMATS[format]
        except KeyError:
            raise ValueError("Unknown unpack format '%s'" % format)

        func = format_info[1]
        func(filename, extract_dir, **dict(format_info[2]))
    else:
        # we need to look at the registered unpackers supported extensions
        format = _find_unpack_format(filename)
        if format is None:
            raise ReadError("Unknown archive format '%s'" % filename)

        func = _UNPACK_FORMATS[format][1]
        kwargs = dict(_UNPACK_FORMATS[format][2])
        func(filename, extract_dir, **kwargs)

# tokenize stuff

cookie_re = re.compile("coding[:=]\s*([-\w.]+)")

def _get_normal_name(orig_enc):
    """Imitates get_normal_name in tokenizer.c."""
    # Only care about the first 12 characters.
    enc = orig_enc[:12].lower().replace("_", "-")
    if enc == "utf-8" or enc.startswith("utf-8-"):
        return "utf-8"
    if enc in ("latin-1", "iso-8859-1", "iso-latin-1") or \
       enc.startswith(("latin-1-", "iso-8859-1-", "iso-latin-1-")):
        return "iso-8859-1"
    return orig_enc

def detect_encoding(readline):
    """
    The detect_encoding() function is used to detect the encoding that should
    be used to decode a Python source file.  It requires one argment, readline,
    in the same way as the tokenize() generator.

    It will call readline a maximum of twice, and return the encoding used
    (as a string) and a list of any lines (left as bytes) it has read in.

    It detects the encoding from the presence of a utf-8 bom or an encoding
    cookie as specified in pep-0263.  If both a bom and a cookie are present,
    but disagree, a SyntaxError will be raised.  If the encoding cookie is an
    invalid charset, raise a SyntaxError.  Note that if a utf-8 bom is found,
    'utf-8-sig' is returned.

    If no encoding is specified, then the default of 'utf-8' will be returned.
    """
    bom_found = False
    encoding = None
    default = 'utf-8'
    def read_or_stop():
        try:
            return readline()
        except StopIteration:
            return ''

    def find_cookie(line):
        try:
            line_string = line.decode('ascii')
        except UnicodeDecodeError:
            return None

        matches = cookie_re.findall(line_string)
        if not matches:
            return None
        encoding = _get_normal_name(matches[0])
        try:
            codec = codecs.lookup(encoding)
        except LookupError:
            # This behaviour mimics the Python interpreter
            raise SyntaxError("unknown encoding: " + encoding)

        if bom_found:
            if codec.name != 'utf-8':
                # This behaviour mimics the Python interpreter
                raise SyntaxError('encoding problem: utf-8')
            encoding += '-sig'
        return encoding

    first = read_or_stop()
    if first.startswith(codecs.BOM_UTF8):
        bom_found = True
        first = first[3:]
        default = 'utf-8-sig'
    if not first:
        return default, []

    encoding = find_cookie(first)
    if encoding:
        return encoding, [first]

    second = read_or_stop()
    if not second:
        return default, [first]

    encoding = find_cookie(second)
    if encoding:
        return encoding, [first, second]

    return default, [first, second]

# functools stuff

def cmp_to_key(mycmp):
    """Convert a cmp= function into a key= function"""
    class K(object):
        __slots__ = ['obj']
        def __init__(self, obj):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
        __hash__ = None
    return K

# os stuff

def fsencode(filename):
    """
    Encode filename to the filesystem encoding with 'surrogateescape' error
    handler, return bytes unchanged. On Windows, use 'strict' error handler if
    the file system encoding is 'mbcs' (which is the default encoding).
    """
    if isinstance(filename, str):
        return filename
    elif isinstance(filename, unicode):
        return filename.encode(sys.getfilesystemencoding())
    else:
        raise TypeError("expect bytes or str, not %s" % type(filename).__name__)
