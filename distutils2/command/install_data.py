"""distutils.command.install_data

Implements the Distutils 'install_data' command, for installing
platform-independent data files."""

# contributed by Bastian Kleineidam


import os
from distutils2.command.cmd import Command
from distutils2.util import change_root, convert_path
from distutils2._backport.sysconfig import get_paths, format_value
from distutils2._backport.shutil import Error

class install_data(Command):

    description = "install data files"

    user_options = [
        ('install-dir=', 'd',
         "base directory for installing data files "
         "(default: installation base dir)"),
        ('root=', None,
         "install everything relative to this alternate root directory"),
        ('force', 'f', "force installation (overwrite existing files)"),
        ]

    boolean_options = ['force']

    def initialize_options(self):
        self.install_dir = None
        self.outfiles = []
        self.data_files_out = []
        self.root = None
        self.force = 0
        self.data_files = self.distribution.data_files
        self.warn_dir = 1

    def finalize_options(self):
        self.set_undefined_options('install_dist',
                                   ('install_data', 'install_dir'),
                                   'root', 'force')

    def run(self):
        self.mkpath(self.install_dir)
        for file in self.data_files.items():
            destination = convert_path(self.expand_categories(file[1]))
            dir_dest = os.path.abspath(os.path.dirname(destination))
            
            self.mkpath(dir_dest)
            try:
                (out, _) = self.copy_file(file[0], dir_dest)
            except Error, e:
                self.warn(e)
                out = destination

            self.outfiles.append(out)
            self.data_files_out.append((file[0], destination))

    def expand_categories(self, path_with_categories):
        local_vars = get_paths()
        local_vars['distribution.name'] = self.distribution.metadata['Name']
        expanded_path = format_value(path_with_categories, local_vars)
        expanded_path = format_value(expanded_path, local_vars)
        if '{' in expanded_path and '}' in expanded_path:
            self.warn("Unable to expand %s, some categories may missing." %
                path_with_categories)
        return expanded_path

    def get_source_files(self):
        return self.data_files.keys()

    def get_inputs(self):
        return self.data_files.keys()

    def get_outputs(self):
        return self.outfiles

    def get_resources_out(self):
        return self.data_files_out
