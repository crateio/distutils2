"""Upload a distribution to a project index."""

import os
import socket
import logging
import platform
import urlparse
from base64 import standard_b64encode
try:
    from hashlib import md5
except ImportError:
    from distutils2._backport.hashlib import md5
from urllib2 import HTTPError
from urllib2 import urlopen, Request

from distutils2 import logger
from distutils2.errors import PackagingOptionError
from distutils2.util import (spawn, read_pypirc, DEFAULT_REPOSITORY,
                             DEFAULT_REALM, encode_multipart)
from distutils2.command.cmd import Command


class upload(Command):

    description = "upload distribution to PyPI"

    user_options = [
        ('repository=', 'r',
         "repository URL [default: %s]" % DEFAULT_REPOSITORY),
        ('show-response', None,
         "display full response text from server"),
        ('sign', 's',
         "sign files to upload using gpg"),
        ('identity=', 'i',
         "GPG identity used to sign files"),
        ('upload-docs', None,
         "upload documentation too"),
        ]

    boolean_options = ['show-response', 'sign']

    def initialize_options(self):
        self.repository = None
        self.realm = None
        self.show_response = False
        self.username = ''
        self.password = ''
        self.show_response = False
        self.sign = False
        self.identity = None
        self.upload_docs = False

    def finalize_options(self):
        if self.repository is None:
            self.repository = DEFAULT_REPOSITORY
        if self.realm is None:
            self.realm = DEFAULT_REALM
        if self.identity and not self.sign:
            raise PackagingOptionError(
                "Must use --sign for --identity to have meaning")
        config = read_pypirc(self.repository, self.realm)
        if config != {}:
            self.username = config['username']
            self.password = config['password']
            self.repository = config['repository']
            self.realm = config['realm']

        # getting the password from the distribution
        # if previously set by the register command
        if not self.password and self.distribution.password:
            self.password = self.distribution.password

    def run(self):
        if not self.distribution.dist_files:
            raise PackagingOptionError(
                "No dist file created in earlier command")
        for command, pyversion, filename in self.distribution.dist_files:
            self.upload_file(command, pyversion, filename)
        if self.upload_docs:
            upload_docs = self.get_finalized_command("upload_docs")
            upload_docs.repository = self.repository
            upload_docs.username = self.username
            upload_docs.password = self.password
            upload_docs.run()

    # XXX to be refactored with register.post_to_server
    def upload_file(self, command, pyversion, filename):
        # Makes sure the repository URL is compliant
        scheme, netloc, url, params, query, fragments = \
            urlparse.urlparse(self.repository)
        if params or query or fragments:
            raise AssertionError("Incompatible url %s" % self.repository)

        if scheme not in ('http', 'https'):
            raise AssertionError("unsupported scheme " + scheme)

        # Sign if requested
        if self.sign:
            gpg_args = ["gpg", "--detach-sign", "-a", filename]
            if self.identity:
                gpg_args[2:2] = ["--local-user", self.identity]
            spawn(gpg_args,
                  dry_run=self.dry_run)

        # Fill in the data - send all the metadata in case we need to
        # register a new release
        f = open(filename, 'rb')
        try:
            content = f.read()
        finally:
            f.close()

        data = self.distribution.metadata.todict()

        # extra upload infos
        data[':action'] = 'file_upload'
        data['protcol_version'] = '1'
        data['content'] = (os.path.basename(filename), content)
        data['filetype'] = command
        data['pyversion'] = pyversion
        data['md5_digest'] = md5(content).hexdigest()

        if command == 'bdist_dumb':
            data['comment'] = 'built for %s' % platform.platform(terse=True)

        if self.sign:
            fp = open(filename + '.asc')
            try:
                sig = fp.read()
            finally:
                fp.close()
            data['gpg_signature'] = [
                (os.path.basename(filename) + ".asc", sig)]

        # set up the authentication
        # The exact encoding of the authentication string is debated.
        # Anyway PyPI only accepts ascii for both username or password.
        user_pass = (self.username + ":" + self.password).encode('ascii')
        auth = "Basic " + standard_b64encode(user_pass)

        # Build up the MIME payload for the POST data
        files = []
        for key in ('content', 'gpg_signature'):
            if key in data:
                filename_, value = data.pop(key)
                files.append((key, filename_, value))

        content_type, body = encode_multipart(data.items(), files)

        logger.info("Submitting %s to %s", filename, self.repository)

        # build the Request
        headers = {'Content-type': content_type,
                   'Content-length': str(len(body)),
                   'Authorization': auth}

        request = Request(self.repository, body, headers)
        # send the data
        try:
            result = urlopen(request)
            status = result.code
            reason = result.msg
        except socket.error, e:
            logger.error(e)
            return
        except HTTPError, e:
            status = e.code
            reason = e.msg

        if status == 200:
            logger.info('Server response (%s): %s', status, reason)
        else:
            logger.error('Upload failed (%s): %s', status, reason)

        if self.show_response and logger.isEnabledFor(logging.INFO):
            sep = '-' * 75
            logger.info('%s\n%s\n%s', sep, result.read().decode(), sep)
