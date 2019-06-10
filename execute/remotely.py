#!/usr/bin/python3

import os
import sys
import subprocess
from .executor import Executor


class RemoteException(Exception):

    def __init__(self, name):
        super().__init__(name)


class RemoteConnectionRefused(RemoteException):

    def __init__(self):
        super().__init__('connection refused')


class RemoteInterpreterMissing(RemoteException):

    def __init__(self, name):
        self.interpreter = name
        super().__init__('missing remote interpreter: {}'.format(name))


class Remotely(Executor):
    def __init__(
            self,
            func,
            hostname,
            port=22,            # ssh port
            user=None,          # ssh username
            password=None,      # ssh password
            key=None,           # ssh private key for auth.
            compression=False,  # ssh uses compression
            quiet=True,        # ssh does not print warning messages
            ssh_options=None,   # extra ssh options to be passed as -o
            python=None,        # python interpreter or current one
            py_options=None):   # extra py arguments to pass to the interpreter
        super().__init__(func, python, py_options, ['remotely.remotely'])
        self.host = hostname
        self.port = port
        self.user = user
        self.password = password
        self.key = key
        self.compression = compression
        self.quiet = quiet
        self.ssh_options = ssh_options

    def _execute(self, script):

        python = self.python or os.path.basename(sys.executable)

        if self.py_options:
            python += ' %s' % self.py_options

        host = self.host

        if self.user:
            host = '{user}@{host}'.format(user=self.user, host=host)

        command = ['ssh']

        if self.port:
            command += ['-p', str(self.port)]

        if self.quiet:
            command += ['-q']

        if self.compression:
            command += ['-C']

        if self.key:
            command += ['-i', self.key]

        if self.ssh_options:
            for name, value in self.ssh_options.items():
                if isinstance(value, bool):
                    command += ['-o', '%s=%s' % (name, 'yes' if value else 'no')]
                else:
                    command += ['-o', '%s=%s' % (name, str(value))]

        command += [host, python]

        with subprocess.Popen(
            command,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
        ) as proc:
            out, err = proc.communicate(script.encode(self.encoding))
            return proc.returncode, out, err

    def _fail(self, err):
        if err:
            if 'Connection closed by remote host' in err:
                raise RemoteConnectionRefused()
            if 'command not found' in err:
                raise RemoteInterpreterMissing(self.python)
            raise RemoteException(err)
        raise RemoteException('remote execution failed')


def remotely(host, *ext_args, **ext_kwargs):
    def wrap(func):
        def wrapped_f(*args, **kwargs):
            return Remotely(func, host, *ext_args, **ext_kwargs)(*args, **kwargs)
        return wrapped_f
    return wrap

