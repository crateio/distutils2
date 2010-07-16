"""
distutils.command.install_dist_info
===================================

:Author: Josip Djolonga
"""

from distutils2.command.cmd import Command
from distutils2 import log
from distutils2._backport.shutil import rmtree

import csv
import hashlib
import os
import re

    
class install_dist_info(Command):
    """Install a .dist-info directory for the package"""

    description = 'Install a .dist-info directory for the package'

    user_options = [
        ('dist-info-dir=', None, 
                           'directory to install the .dist-info directory to'),
        ('installer=', None, 'the name of the installer'),
        ('no-dist-requested', None, 'do not generate a REQUESTED file'),
        ('no-dist-record', None, 'do not generate a RECORD file'),
    ]
    
    boolean_options = [
        'no-dist-requested',
        'no-dist-record',
    ]

    def initialize_options(self):
        self.dist_info_dir = None
        self.installer = None
        self.no_dist_requested = False
        self.no_dist_record = False

    def finalize_options(self):
        self.set_undefined_options('install_lib',
                                   ('install_dir', 'dist_info_dir'))

        if self.installer is None:
            self.installer = 'distribute'
        
        metadata = self.distribution.metadata

        basename = "%s-%s.dist-info" % (
            to_filename(safe_name(metadata['Name'])),
            to_filename(safe_version(metadata['Version'])),
        )

        self.distinfo_dir = os.path.join(self.dist_info_dir, basename)
        self.outputs = []

    def run(self):
        target = self.distinfo_dir
        if os.path.isdir(target) and not os.path.islink(target) \
           and not self.dry_run:
           rmtree(target)
        elif os.path.exists(target):
            self.execute(os.unlink, (self.distinfo_dir,), "Removing " + target)

        if not self.dry_run:
            self.execute(os.makedirs, (target,), "Creating " + target)

            metadata_path = os.path.join(self.distinfo_dir, 'METADATA')
            log.info('Creating %s' % (metadata_path,))
            self.distribution.metadata.write(metadata_path)
            self.outputs.append(metadata_path)
            
            installer_path = os.path.join(self.distinfo_dir, 'INSTALLER')
            log.info('Creating %s' % (installer_path,))
            f = open(installer_path, 'w')
            f.write(self.installer)
            f.close()
            self.outputs.append(installer_path)

            if not self.no_dist_requested:
                requested_path = os.path.join(self.distinfo_dir, 'REQUESTED')
                log.info('Creating %s' % (requested_path,))
                f = open(requested_path, 'w')
                f.close()
                self.outputs.append(requested_path)

            if not self.no_dist_record:
                record_path = os.path.join(self.distinfo_dir, 'RECORD')
                log.info('Creating %s' % (record_path,))
                f = open(record_path, 'wb')
                writer = csv.writer(f, delimiter=',',
                                       lineterminator=os.linesep,
                                       quotechar='"')
                
                install = self.get_finalized_command('install')
                
                for fpath in install.get_outputs():
                    if fpath.endswith('.pyc'):
                        continue
                        # FIXME, in get_outputs() missing .pyc files exist
                    size = os.path.getsize(fpath)
                    fd = open(fpath, 'r')
                    hash = hashlib.md5()
                    hash.update(fd.read())
                    md5sum = hash.hexdigest()
                    writer.writerow((fpath, md5sum, size))
                    
                writer.writerow((record_path, '', ''))
                self.outputs.append(record_path)
                
                f.close()
                
    def get_outputs(self):
        return self.outputs


# The following routines are taken from setuptools' pkg_resources module and
# can be replaced by importing them from pkg_resources once it is included
# in the stdlib.

def safe_name(name):
    """Convert an arbitrary string to a standard distribution name

    Any runs of non-alphanumeric/. characters are replaced with a single '-'.
    """
    return re.sub('[^A-Za-z0-9.]+', '-', name)


def safe_version(version):
    """Convert an arbitrary string to a standard version string

    Spaces become dots, and all other non-alphanumeric characters become
    dashes, with runs of multiple dashes condensed to a single dash.
    """
    version = version.replace(' ','.')
    return re.sub('[^A-Za-z0-9.]+', '-', version)


def to_filename(name):
    """Convert a project or version name to its filename-escaped form

    Any '-' characters are currently replaced with '_'.
    """
    return name.replace('-','_')
