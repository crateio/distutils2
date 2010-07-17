"""
distutils.command.install_distinfo
==================================

:Author: Josip Djolonga

This module implements the ``install_distinfo`` command that creates the
``.dist-info`` directory for the distribution, as specified in :pep:`376`.
Usually, you do not have to call this command directly, it gets called
automatically by the ``install`` command.
"""

from distutils2.command.cmd import Command
from distutils2 import log
from distutils2._backport.shutil import rmtree


import csv
import hashlib
import os
import re


class install_distinfo(Command):
    """Install a .dist-info directory for the package"""

    description = 'Install a .dist-info directory for the package'

    user_options = [
        ('dist-info-dir=', None,
                           'directory where the the .dist-info directory will '
                           'be installed'),
        ('installer=', None, 'the name of the installer'),
        ('requested', None, 'generate a REQUESTED file'),
        ('no-requested', None, 'do not generate a REQUESTED file'),
        ('no-dist-record', None, 'do not generate a RECORD file'),
    ]

    boolean_options = [
        'requested',
        'no-dist-record',
    ]

    negative_opt = {'no-requested': 'requested'}

    def initialize_options(self):
        self.distinfo_dir = None
        self.installer = None
        self.requested = None
        self.no_distinfo_record = None

    def finalize_options(self):
        self.set_undefined_options('install',
                                   ('distinfo_dir', 'distinfo_dir'),
                                   ('installer', 'installer'),
                                   ('requested', 'requested'),
                                   ('no_distinfo_record',
                                        'no_distinfo_record'))

        self.set_undefined_options('install_lib',
                                   ('install_dir', 'distinfo_dir'))

        if self.installer is None:
            self.installer = 'distutils'
        if self.requested is None:
            self.requested = True
        if self.no_distinfo_record is None:
            self.no_distinfo_record = False

        metadata = self.distribution.metadata

        basename = "%s-%s.dist-info" % (
            to_filename(safe_name(metadata['Name'])),
            to_filename(safe_version(metadata['Version'])),
        )

        self.distinfo_dir = os.path.join(self.distinfo_dir, basename)
        self.outputs = []

    def run(self):
        if not self.dry_run:
            target = self.distinfo_dir

            if os.path.isdir(target) and not os.path.islink(target):
                rmtree(target)
            elif os.path.exists(target):
                self.execute(os.unlink, (self.distinfo_dir,),
                             "Removing " + target)

            self.execute(os.makedirs, (target,), "Creating " + target)

            metadata_path = os.path.join(self.distinfo_dir, 'METADATA')
            log.info('Creating %s' % (metadata_path,))
            self.distribution.metadata.write(metadata_path)
            self.outputs.append(metadata_path)

            installer_path = os.path.join(self.distinfo_dir, 'INSTALLER')
            log.info('Creating %s' % (installer_path,))
            f = open(installer_path, 'w')
            try:
                f.write(self.installer)
            finally:
                f.close()
            self.outputs.append(installer_path)

            if self.requested:
                requested_path = os.path.join(self.distinfo_dir, 'REQUESTED')
                log.info('Creating %s' % (requested_path,))
                f = open(requested_path, 'w')
                f.close()
                self.outputs.append(requested_path)

            if not self.no_distinfo_record:
                record_path = os.path.join(self.distinfo_dir, 'RECORD')
                log.info('Creating %s' % (record_path,))
                f = open(record_path, 'wb')
                try:
                    writer = csv.writer(f, delimiter=',',
                                           lineterminator=os.linesep,
                                           quotechar='"')

                    install = self.get_finalized_command('install')

                    for fpath in install.get_outputs():
                        if fpath.endswith('.pyc') or fpath.endswith('.pyo'):
                            # do not put size and md5 hash, as in PEP-376
                            writer.writerow((fpath, '', ''))
                        else:
                            size = os.path.getsize(fpath)
                            fd = open(fpath, 'r')
                            hash = hashlib.md5()
                            hash.update(fd.read())
                            md5sum = hash.hexdigest()
                            writer.writerow((fpath, md5sum, size))

                    # add the RECORD file itself
                    writer.writerow((record_path, '', ''))
                    self.outputs.append(record_path)
                finally:
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
    version = version.replace(' ', '.')
    return re.sub('[^A-Za-z0-9.]+', '-', version)


def to_filename(name):
    """Convert a project or version name to its filename-escaped form

    Any '-' characters are currently replaced with '_'.
    """
    return name.replace('-', '_')
