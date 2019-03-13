#!/usr/bin/python3

import os, sys, re, inspect, subprocess, types, logging, pickle
from functools import wraps


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

#
# The remote script is in the form (not exactly)
#  ```
#  import foundamental modules  # there are some foundamental modules that we cannot avoid
#
#  stdout('---- separator ----')  # if ssh printed something we can separate it from the script's output stream
#  stderr('---- separator ----')  # as for the error stream
#
#  for module in [deduced modules]  # deduced modules are dynamically loaded using importlib
#    try import module              # failing to import a module is not considered a failure
#
#  def foo(*args, **kwargs):  # this being the function to invoke
#    ..
#
#  x = foo(...)                   # here the function in invoked, the return value stored and any stderr/stdout data confined 
#  stdout('---- separator ----')  # again we output a separator to separate the script's output from the returned value
#  stdout(serialize(x))           # and finally we serialize the returned value using the output stream
#  ```

# So the output will be something like:
#
#       [STDOUT]                 [STDERR]
#
# ssh stdout (if any)    | ssh stdout (if any)
# ----- separator ------ | ----- separator ------
# script stdout (if any) | script stderr (if any)
# ----- separator ------ |
# script returned value  |
#

class Remote:

    def __init__(self, func, hostname,
        port=22,  # ssh port
        user=None,  # ssh username
        password=None,  # ssh password
        key=None,  # ssh private key for auth.
        compression=False,  # ssh uses compression
        quiet=False,  # ssh does not print warning messages
        ssh_options=None,  # extra ssh options to be passed as -o
        python=None,  # python interpreter or current one
        py_options=None  # extra py arguments to pass to the interpreter
    ):
        self.func = func
        self.host = hostname
        self.port = port
        self.user = user
        self.password = password
        self.key = key
        self.compression = compression
        self.quiet = quiet
        self.ssh_options = ssh_options
        self.python = python
        self.py_options = py_options
        self.out = Remote._default_out
        self.err = Remote._default_err

    @staticmethod
    def _default_out(out):
        sys.stdout.buffer.write(out)

    @staticmethod
    def _default_err(out):
        sys.stderr.buffer.write(out)

    @staticmethod
    def _gen_source(func):
        '''1) get the function source code
        2) remove any "@remote.remotely(...)" decorator
        3) reindent the code as if the function was top-level
        :param func the function to process
        :return the code and the indentation (both as strings)
        '''
        source = inspect.getsource(func)
        source = re.sub(r'@(remote\.)?remotely\([^)]+\)\s*', '', source)
        lines = source.split('\n')
        count = len(lines[0]) - len(lines[0].lstrip())
        indent = lines[0][:count]
        lines = [line[count:] for line in lines]
        return ('\n'.join(lines), indent)

    def __call__(self, *args, **kwargs):
        python = self.python if self.python else os.path.basename(sys.executable)
        python += '' if not self.py_options else ' %s' % self.py_options
        funcname = self.func.__name__
        modules = [val.__name__ for name, val in globals().items() if isinstance(val, types.ModuleType)]
        encoding = 'utf-8'
        separator = '---------- 6262f79e1f287a957cc5d8b ----------'
        source_fmt = '''
import sys, pickle, importlib

sys.stdout.buffer.write(b'{separator}')
sys.stdout.flush()
sys.stderr.buffer.write(b'{separator}')
sys.stderr.flush()

for mod in {modules}:
{I}try:
{I}{I}vars()[mod] = importlib.import_module(mod)
{I}except Exception as ex:
{I}{I}sys.stderr.write(str(ex))

{code}

de8e812d3bd = {funcname}(*{args}, **{kwargs})
sys.stdout.flush()
sys.stdout.buffer.write(b'{separator}')
sys.stdout.buffer.write(pickle.dumps(de8e812d3bd))
'''
        code, indent = self._gen_source(self.func)

        script = source_fmt.format(
            modules=modules,
            code=code,
            funcname=funcname,
            separator=separator,
            I=indent,
            args=str(args),
            kwargs=str(kwargs)
        )

        host = '{user}@{host}'.format(
            user=self.user,
            host=self.host
        ) if self.user else self.host
        
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
            out, err = proc.communicate(script.encode(encoding))
            returncode = proc.returncode

        if returncode is not 0:
            if err:
                if 'Connection closed by remote host' in err.decode(encoding):
                    raise RemoteConnectionRefused()
                if '{}: command not found'.format(python) in err.decode(encoding):
                    raise RemoteInterpreterMissing(python)
                raise RemoteException(err)
            raise RemoteException('remote execution failed')
    
        ret = None
    
        if out:
            spl = out.split(separator.encode(encoding))
            pre = spl[0]  # ssh output
            out = spl[1]  # script output
            ret = spl[2]  # return value
            if pre:
                logging.info(pre)
            if out:
                self.out(out)
    
        if err:
            spl = err.split(separator.encode(encoding))
            pre = spl[0]  # ssh output
            err = spl[1]  # script output
            if pre:
                logging.warning(pre)
            if err:
                self.err(err)

        if ret:
            logging.debug(ret)
            ret = pickle.loads(ret)
    
        return ret


def remotely(host, *ext_args, **ext_kwargs):
    def wrap(func):
        def wrapped_f(*args, **kwargs):
            return Remote(func, host, *ext_args, **ext_kwargs)(*args, **kwargs)
        return wrapped_f
    return wrap

