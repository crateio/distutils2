"""Create the PEP 376-compliant .dist-info directory."""

# Forked from the former install_egg_info command by Josip Djolonga

import os
import csv
import codecs
try:
    import hashlib
except ImportError:
    from distutils2._backport import hashlib

from distutils2 import logger
from distutils2.command.cmd import Command
from distutils2._backport.shutil import rmtree


class install_distinfo(Command):

    description = 'create a .dist-info directory for the distribution'

    user_options = [
        ('install-dir=', None,
         "directory where the the .dist-info directory will be created"),
        ('installer=', None,
         "the name of the installer"),
        ('requested', None,
         "generate a REQUESTED file"),
        ('no-requested', None,
         "do not generate a REQUESTED file"),
        ('no-record', None,
         "do not generate a RECORD file"),
        ('no-resources', None,
         "do not generate a RESOURCES file"),
    ]

    boolean_options = ['requested', 'no-record', 'no-resources']

    negative_opt = {'no-requested': 'requested'}

    def initialize_options(self):
        self.install_dir = None
        self.installer = None
        self.requested = None
        self.no_record = None
        self.no_resources = None
        self.outfiles = []

    def finalize_options(self):
        self.set_undefined_options('install_dist',
                                   'installer', 'requested', 'no_record')

        self.set_undefined_options('install_lib', 'install_dir')

        if self.installer is None:
            # FIXME distutils or packaging or distutils2?
            # + document default in the option help text above and in install
            self.installer = 'distutils'
        if self.requested is None:
            self.requested = True
        if self.no_record is None:
            self.no_record = False
        if self.no_resources is None:
            self.no_resources = False

        metadata = self.distribution.metadata

        basename = metadata.get_fullname(filesafe=True) + ".dist-info"

        self.install_dir = os.path.join(self.install_dir, basename)

    def run(self):
        target = self.install_dir

        if os.path.isdir(target) and not os.path.islink(target):
            if not self.dry_run:
                rmtree(target)
        elif os.path.exists(target):
            self.execute(os.unlink, (self.install_dir,),
                         "removing " + target)

        self.execute(os.makedirs, (target,), "creating " + target)

        metadata_path = os.path.join(self.install_dir, 'METADATA')
        self.execute(self.distribution.metadata.write, (metadata_path,),
                     "creating " + metadata_path)
        self.outfiles.append(metadata_path)

        installer_path = os.path.join(self.install_dir, 'INSTALLER')
        logger.info('creating %s', installer_path)
        if not self.dry_run:
            f = open(installer_path, 'w')
            try:
                f.write(self.installer)
            finally:
                f.close()
        self.outfiles.append(installer_path)

        if self.requested:
            requested_path = os.path.join(self.install_dir, 'REQUESTED')
            logger.info('creating %s', requested_path)
            if not self.dry_run:
                open(requested_path, 'wb').close()
            self.outfiles.append(requested_path)

        if not self.no_resources:
            install_data = self.get_finalized_command('install_data')
            if install_data.get_resources_out() != []:
                resources_path = os.path.join(self.install_dir,
                                              'RESOURCES')
                logger.info('creating %s', resources_path)
                if not self.dry_run:
                    f = open(resources_path, 'w')
                    try:
                        writer = csv.writer(f, delimiter=',',
                                            lineterminator='\n',
                                            quotechar='"')
                        for row in install_data.get_resources_out():
                            writer.writerow(row)
                    finally:
                        f.close()

                self.outfiles.append(resources_path)

        if not self.no_record:
            record_path = os.path.join(self.install_dir, 'RECORD')
            logger.info('creating %s', record_path)
            if not self.dry_run:
                f = codecs.open(record_path, 'w', encoding='utf-8')
                try:
                    writer = csv.writer(f, delimiter=',',
                                        lineterminator='\n',
                                        quotechar='"')

                    install = self.get_finalized_command('install_dist')

                    for fpath in install.get_outputs():
                        if fpath.endswith('.pyc') or fpath.endswith('.pyo'):
                            # do not put size and md5 hash, as in PEP-376
                            writer.writerow((fpath, '', ''))
                        else:
                            size = os.path.getsize(fpath)
                            fp = open(fpath, 'rb')
                            try:
                                hash = hashlib.md5()
                                hash.update(fp.read())
                            finally:
                                fp.close()
                            md5sum = hash.hexdigest()
                            writer.writerow((fpath, md5sum, size))

                    # add the RECORD file itself
                    writer.writerow((record_path, '', ''))
                finally:
                    f.close()
            self.outfiles.append(record_path)

    def get_outputs(self):
        return self.outfiles
