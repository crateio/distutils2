import os.path
from distutils2.core import Command

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
