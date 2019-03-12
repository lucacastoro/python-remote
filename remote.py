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
  __slots__ = ('interpreter')
  def __init__(self, name):
    self.interpreter = name
    super().__init__('missing remote interpreter: {}'.format(name))


class Remote:

  def __init__(self, hostname,
      port=22, # ssh port
      user=None, # ssh username
      password=None, # ssh password
      key=None, # ssh private key for auth.
      compression=False, # ssh uses compression
      quiet=True, # ssh does not print warning messages
      ssh_options=None, # extra ssh options to be passed as -o
      python=None, # python interpreter or current one
      py_options=None): # extra py arguments to pass to the interpreter
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

  @staticmethod
  def _get_source(func):
    source = inspect.getsource(func)
    source = re.sub(r'@(remote\.)?remotize\([^)]+\)\s*', '', source)
    lines = source.split('\n')
    indent = len(lines[0]) - len(lines[0].lstrip())
    lines = [ l[indent:] for l in lines]
    return '\n'.join(lines)

  @staticmethod
  def _gen_imports(modules):
    return '''import sys, pickle, importlib
for mod in {mods}:
  try:
    vars()[mod] = importlib.import_module(mod)
  except:
    pass'''.format(mods=str(modules))

  def __call__(self, func, *args, **kwargs):
    python = self.python if self.python else os.path.basename(sys.executable)
    python += '' if not self.py_options else ' %s' % self.py_options
    funcname = func.__name__
    modules = [val.__name__ for name, val in globals().items() if isinstance(val, types.ModuleType)]
    encoding = 'utf-8'
    separator = '---------- 6262f79e1f287a957cc5d8b ----------'

    source = '''
{imports}

{code}

de8e812d3bd = {funcname}(*{args}, **{kwargs})
sys.stdout.flush()
sys.stdout.buffer.write(b'{separator}')
sys.stdout.buffer.write(pickle.dumps(de8e812d3bd))
'''.format(imports=self._gen_imports(modules), code=self._get_source(func), funcname=funcname, separator=separator, args=str(args), kwargs=str(kwargs))

    logging.debug(source)

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
  
    logging.debug('Remote, executing: {}\n{}'.format(' '.join(command), source))

    with subprocess.Popen(
      command,
      shell=False,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      stdin=subprocess.PIPE,
    ) as proc:
      out, err = proc.communicate(source.encode(encoding))
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
      out = out.split(separator.encode(encoding))
      ret = out[1]
      out = out[0]
      sys.stdout.buffer.write(out)
  
    if err:
      sys.stderr.buffer.write(err)
  
    if ret:
      logging.debug(ret)
      ret = pickle.loads(ret)
  
    return ret

def remotely(host, func, interpreter=None, user=None, port=22, py_options='', ssh_options=''):
  Remote(host, port=port, user=user, ssh_options=ssh_options)(func, interpreter, py_options=py_options)

def remotize(host, *ext_args, **ext_kwargs):
  def wrap(func):
    def wrapped_f(*args, **kwargs):
      return Remote(host, *ext_args, **ext_kwargs)(func, *args, **kwargs)
    return wrapped_f
  return wrap

