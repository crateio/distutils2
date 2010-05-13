import os.path, tempfile, zipfile
from distutils2.core import Command

def zip_dir_into(directory, destination):
    """Compresses recursively contents of directory into a zipfile located
    under given destination.
    """
    zip_file = zipfile.ZipFile(destination, "w")
    for root, dirs, files in os.walk(directory):
        for name in files:
            full = os.path.join(root, name)
            relative = root[len(directory):].lstrip(os.path.sep)
            dest = os.path.join(relative, name)
            zip_file.write(full, dest)
    zip_file.close()

class upload_docs(Command):

    user_options = [
        ('upload-dir=', None, 'directory to upload'),
        ]

    def initialize_options(self):
        self.upload_dir = None

    def finalize_options(self):
        if self.upload_dir == None:
            build = self.get_finalized_command('build')
            self.upload_dir = os.path.join(build.build_base, "docs")

    def run(self):
        pass
