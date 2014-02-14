# Copyright (c) 2013 Ask.com.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy
# of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.
#
# Any express or implied warranties, including, without limitation, the implied
# warranties of merchantability and fitness for a particular purpose and any
# warranty of non-infringement are disclaimed.  The copyright owner and
# contributors shall not be liable for any direct, indirect, incidental,
# special, punitive, exemplary, or consequential damages (including, without
# limitation, procurement of substitute goods or services; loss of use, data or
# profits; or business interruption) however caused and under any theory of
# liability, whether in contract, strict liability, or tort (including
# negligence) or otherwise arising in any way out of the use of or inability to
# use the software, even if advised of the possibility of such damage.  The
# foregoing limitations of liability shall apply even if deemed to fail of
# their essential purpose.  The software may only be distributed under the
# terms of the License and this disclaimer.
''' Execute commands on remote hosts '''

import uuid
import socket
import subprocess
import logging

import paramiko
logging.getLogger("paramiko").setLevel(logging.WARNING)


from woodstove import exceptions
from woodstove.common import config, logger


class Output(object):
    ''' Return value of most Command class methods '''
    stdout = None
    stderr = None
    code = None

    def dict(self):
        return self.__dict__


class Command(object):
    client = None

    def __init__(self, target, port=22, user=None, verify_keys=False,
                 default_timeout=None):
        self.timeout = default_timeout
        if not user:
            user = config.Config().woodstove.command.default_user
        logger.Logger(__name__).info("Connecting to: %s@%s:%d" % (user, target, port))
        self.client = paramiko.SSHClient()
        if verify_keys:
            self.client.load_system_host_keys()
        else:
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(target, username=user, port=port)
        except (paramiko.SSHException,
                paramiko.AuthenticationException) as exep:
            raise exceptions.CommandException(exep.message)

    def execute(self, command, timeout=None):
        ''' Run command with optional timout '''
        logger.Logger(__name__).info("Executing command: %s" % command)
        out = Output()
        if not timeout and self.timeout:
            timeout = self.timeout
        (stdin, stdout, stderr) = self.client.exec_command(command,
                                                           timeout=timeout)
        try:
            out.stdout = stdout.read()
            out.stderr = stderr.read()
        except socket.timeout:
            self.client.get_transport().close()
            raise exceptions.TimeoutException
        out.code = stdout.channel.recv_exit_status()
        stdout.close()
        stderr.close()
        stdin.close()
        return out

    def push(self, source, destpath, timeout=None):
        ''' Push file to target with optional timeout '''
        logger.Logger(__name__).info("Pushing file to: %s" % destpath)
        if not timeout and self.timeout:
            timeout = self.timeout

        sftp = self.client.open_sftp()
        sftp.get_channel().settimeout(timeout)
        try:
            sftp.putfo(source, destpath)
            out = Output()
            out.code = 0
            return out
        except socket.timeout:
            self.client.get_transport().close()
            raise exceptions.TimeoutException

    def pull(self, sourcepath, target, timeout=None):
        ''' Pull file from target with optional timeout '''
        logger.Logger(__name__).info("Pulling file: %s" % sourcepath)
        out = Output()
        if not timeout and self.timeout:
            timeout = self.timeout

        sftp = self.client.open_sftp()
        sftp.get_channel().settimeout(timeout)
        try:
            return sftp.getfo(sourcepath, target)
        except socket.timeout:
            self.client.get_transport().close()
            raise exceptions.TimeoutException

    def chmod(self, path, mode, timeout=None):
        ''' Chmod file on target '''
        logger.Logger(__name__).info("Chmoding %s to %d" % (path, mode))
        sftp = self.client.open_sftp()
        sftp.get_channel().settimeout(timeout)
        try:
            sftp.chmod(path, mode)
        except socket.timeout:
            self.client.get_transport().close()
            raise exceptions.TimeoutException

    def rm(self, path, timeout=None):
        ''' Remove file on target '''
        logger.Logger(__name__).info("Deleting file: %s" % path)
        sftp = self.client.open_sftp()
        sftp.get_channel().settimeout(timeout)
        try:
            sftp.remove(path)
        except socket.timeout:
            self.client.get_transport().close()
            raise exceptions.TimeoutException

    def execute_script(self, script, timeout=None):
        ''' Push script to target and execute it '''
        logger.Logger(__name__).info("Executing script")
        with RemoteTemp(self, script) as temp:
            return self.execute(temp.path, timeout)


class RemoteTemp(object):
    path = None

    def __init__(self, command, source):
        self.command = command
        self.source = source

    def __enter__(self):
        self.path = '/tmp/' + str(uuid.uuid4())
        logger.Logger(__name__).info("Creating remote temp file")
        self.command.push(self.source, self.path)
        self.command.chmod(self.path, 0775)
        return self

    def __exit__(self, *_):
        self.command.rm(self.path)


def execute(cmd):
    ''' Execute command localy (on the woodstove server) '''
    logger.Logger(__name__).info("Executing (local): %s" % cmd)
    out = Output()
    process = subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out.stdout, out.stderr = process.communicate()
    out.code = process.returncode
    return out
