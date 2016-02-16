from pecan import expose, request, response
from webob.static import FileIter
from ceph_installer.util import make_setup_script, mkdir
from ceph_installer import process
from ceph_installer.controllers import error
import os
from StringIO import StringIO
import logging

logger = logging.getLogger(__name__)


class SetupController(object):

    @expose(content_type='application/octet-stream')
    def index(self):
        script = make_setup_script(request.url)
        response.headers['Content-Disposition'] = 'attachment; filename=setup.sh'
        response.app_iter = FileIter(script)

    @expose(content_type='application/octet-stream')
    def agent(self):
        script = make_setup_script(request.url)
        response.headers['Content-Disposition'] = 'attachment; filename=agent-setup.sh'
        response.app_iter = FileIter(script)

    @expose(content_type='application/octet-stream')
    def key(self):
        """
        Serves the public SSH key for the user that own the current service
        """
        # look for the ssh key of the current user
        private_key_path = os.path.expanduser('~/.ssh/id_rsa')
        public_key_path = os.path.expanduser('~/.ssh/id_rsa.pub')
        ssh_dir = os.path.dirname(public_key_path)

        if not os.path.isdir(ssh_dir):
            logger.warning('.ssh directory not found, creating one at: %s', ssh_dir)
            mkdir(ssh_dir)

        # if there isn't one create it
        if not os.path.exists(public_key_path):
            logger.warning('expected public key not found: %s', public_key_path)
            logger.warning('will create new ssh key pair')
            # create one
            command = [
                    'ssh-keygen', '-q', '-t', 'rsa',
                    '-N', '',
                    '-f', private_key_path,
            ]
            out, err, code = process.run(command, send_input='y\n')
            if code != 0:
                error(500, err)

        # define the file to download
        response.headers['Content-Disposition'] = 'attachment; filename=id_rsa.pub'
        with open(public_key_path) as key_contents:
            key = StringIO()
            key.write(key_contents.read())
            key.seek(0)
        response.app_iter = FileIter(key)
