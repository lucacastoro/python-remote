#!/usr/bin/python3

import os, sys, re, inspect, subprocess, types, logging, pickle
from functools import wraps


class DockerException(Exception):

    def __init__(self, name):
        super().__init__(name)

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

class Executor:

    def __init__(self, func, python=None, py_options=None, decorators=[]):
        self.func = func
        self.python = python
        self.py_options = py_options
        self.decorators = decorators

    def _out(self, out):
        sys.stdout.buffer.write(out)

    def _err(self, out):
        sys.stderr.buffer.write(out)

    def _gen_source(self, func):
        '''1) get the function source code
        2) remove any "@remote.remotely(...)" decorator
        3) reindent the code as if the function was top-level
        :param func the function to process
        :return the code and the indentation (both as strings)
        '''
        source = inspect.getsource(func)
        for decorator in self.decorators:
            pair = decorator.split('.')
            module = pair[0]
            name = pair[1]
            source = re.sub(r'@(' + module + r'\.)?' + name + r'\([^)]+\)\s*', '', source)
        lines = source.split('\n')
        count = len(lines[0]) - len(lines[0].lstrip())
        indent = lines[0][:count]
        lines = [line[count:] for line in lines]
        return ('\n'.join(lines), indent)

    def __call__(self, *args, **kwargs):
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

        code, out, err = self._execute(script)

        if code is not 0:
            if err:
                raise Exception(err)
            raise Exception('remote execution failed')
    
        ret = None

        if out:
            spl = out.split(separator.encode(encoding))
            pre = spl[0]  # ssh output
            out = spl[1]  # script output
            ret = spl[2]  # return value
            if pre:
                logging.info(pre)
            if out:
                self._out(out)
    
        if err:
            spl = err.split(separator.encode(encoding))
            pre = spl[0]  # ssh output
            err = spl[1]  # script output
            if pre:
                logging.warning(pre)
            if err:
                self._err(err)

        if ret:
            logging.debug(ret)
            ret = pickle.loads(ret)
    
        return ret

class Docker(Executor):

    def __init__(self, func, image, tag='latest', python=None, py_options=None):
        super().__init__(func, python, py_options, ['docker.dockerly'])
        self.image = image
        self.tag = tag
        pass

    def _execute(self, script):

        python = self.python or 'python3'
        if self.py_options:
            python += ' ' + self.py_options
        local_script = '/tmp/asdasdasd.py'
        remote_script = local_script

        command = [
            'docker', 'run', '-i', '--rm',
            "{image}:{tag}".format(image=self.image, tag=self.tag),
            python
        ]

        with subprocess.Popen(
            command,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
        ) as proc:
            out, err = proc.communicate(script.encode('utf-8'))
            return proc.returncode, out, err


def dockerly(*ext_args, **ext_kwargs):
    def wrap(func):
        def wrapped_f(*args, **kwargs):
            return Docker(func, *ext_args, **ext_kwargs)(*args, **kwargs)
        return wrapped_f
    return wrap

