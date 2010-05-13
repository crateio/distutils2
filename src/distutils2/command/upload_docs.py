import base64, httplib, os.path, tempfile, urlparse, zipfile
from cStringIO import StringIO
from distutils2 import log
from distutils2.core import Command

def zip_dir(directory):
    """Compresses recursively contents of directory into a StringIO object"""
    destination = StringIO()
    zip_file = zipfile.ZipFile(destination, "w")
    for root, dirs, files in os.walk(directory):
        for name in files:
            full = os.path.join(root, name)
            relative = root[len(directory):].lstrip(os.path.sep)
            dest = os.path.join(relative, name)
            zip_file.write(full, dest)
    zip_file.close()
    return destination

# grabbed from
#    http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/
def encode_multipart(fields, files, boundary=None):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
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
    for (key, filename, value) in files:
        l.extend([
            '--' + boundary,
            'Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename),
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
        tmp_dir = tempfile.mkdtemp()
        name = self.distribution.metadata['Name']
        zip_file = zip_dir(self.upload_dir)

        fields = {':action': 'doc_upload', 'name': name}.items()
        files = [('content', name, zip_file.getvalue())]
        content_type, body = encode_multipart(fields, files)

        credentials = self.username + ':' + self.password
        auth = "Basic " + base64.encodestring(credentials).strip()

        self.announce("Submitting documentation to %s" % (self.repository),
                      log.INFO)

        schema, netloc, url, params, query, fragments = \
            urlparse.urlparse(self.repository)
        conn = httplib.HTTPConnection(netloc)

        try:
            conn.connect()
            conn.putrequest("POST", url)
            conn.putheader('Content-type', content_type)
            conn.putheader('Content-length', str(len(body)))
            conn.putheader('Authorization', auth)
            conn.endheaders()
            conn.send(body)
        except socket.error, e:
            self.announce(str(e), log.ERROR)
            return

        r = conn.getresponse()
