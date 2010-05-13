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

# grabbed from
#    http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/
def encode_multipart(fields, files, boundary=None):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, content_type, value)
                            elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    if boundary is None:
        boundary = '--------------GHSKFJDLGDS7543FJKLFHRE75642756743254'
    CRLF = '\r\n'
    l = []
    for (key, value) in fields:
        l.extend([
            '--' + boundary,
            'Content-Disposition: form-data; name="%s"' % key,
            '',
            value])
    for (key, filename, content_type, value) in files:
        l.extend([
            '--' + boundary,
            'Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename),
            'Content-Type: %s' % content_type,
            '',
            value])
    l.append('--' + boundary + '--')
    l.append('')
    body = CRLF.join(l)
    content_type = 'multipart/form-data; boundary=%s' % boundary
    return content_type, body

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
