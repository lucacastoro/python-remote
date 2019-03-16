#!/usr/bin/python3

import os, sys, re, inspect, types, logging, pickle
import math
from functools import wraps

#
# The script is in the form (not exactly)
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
        self.encoding = 'utf-8'

    def _out(self, out):
        sys.stdout.write(out)

    def _err(self, out):
        sys.stderr.write(out)

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

    @staticmethod
    def _print_script(script):
        lines = script.split('\n')
        fmt = '%0{}d %s'.format(1 + int(math.log(len(lines), 10)))
        for num in range(len(lines)):
            print(fmt % (num + 1, lines[num]))

    def __call__(self, *args, **kwargs):
        funcname = self.func.__name__
        modules = [val.__name__ for name, val in globals().items() if isinstance(val, types.ModuleType)]
        separator = '---------- 6262f79e1f287a957cc5d8b ----------'
        source_fmt = '''import sys, pickle, importlib

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

e1732ceb4f6 = pickle.loads({args_dump})
a1e46c610ca = pickle.loads({kwargs_dump})
de8e812d3bd = {funcname}(*e1732ceb4f6, **a1e46c610ca)
sys.stdout.flush()
sys.stdout.buffer.write(b'{separator}')
sys.stdout.buffer.write(pickle.dumps(de8e812d3bd))'''

        code, indent = self._gen_source(self.func)

        script = source_fmt.format(
            modules=modules,
            code=code,
            funcname=funcname,
            separator=separator,
            I=indent,
            args_dump=pickle.dumps(args),
            kwargs_dump=pickle.dumps(kwargs)
        )

        code, out, err = self._execute(script)

        if err:
            err = err.split(separator.encode(self.encoding))
            run_error = err[0].decode(self.encoding) if len(out) > 0 else None
            scr_error = err[1].decode(self.encoding) if len(err) > 1 else None

        if out:
            out = out.split(separator.encode(self.encoding))
            run_output = out[0].decode(self.encoding) if len(out) > 0 else None
            scr_output = out[1].decode(self.encoding) if len(out) > 1 else None
            ret_object = pickle.loads(out[2]) if len(out) > 2 else None
        
        if code is not 0:
            if run_error:
                raise self._fail(run_error)
            if scr_error:
                raise self._fail(scr_error)
            raise self._fail('execution failed, return code: {}'.format(code))
    
        if run_output:                # if the underlying executor said something
            logging.info(run_output)  # just report it

        if scr_output:                # the script output instead
            self._out(scr_output)     # will go to stdout
    
        if run_error:                   # if the executor printed something to stder
            logging.warning(run_error)  # just log it

        if scr_error:             # if instead it was the script itself
            self._err(scr_error)  # redirect it to stderr
        
        return ret_object
