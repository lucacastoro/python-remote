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
    super().__init__(f'missing remote interpreter: {name}')


class Remote:

  def __init__(self, host, port=22, user=None, ssh_options=None):
    self.host = host
    self.port = port
    self.user = user
    self.ssh_options = ssh_options
    pass

  def __call__(self, func, python=None, py_options=None):
    if not python:
      python = os.path.basename(sys.executable)

    funcname = func.__name__
    modules = (val.__name__ for name, val in globals().items() if isinstance(val, types.ModuleType))
    imports = 'import sys, pickle'
    encoding = 'utf-8'
    source = inspect.getsource(func)
    separator = '---------- separator ----------'
    for module in modules:
      if module not in ['pickle', 'sys']:
        imports += f"""
try:
  import {module}
except:
  pass
"""

    wrapper = f"""
de8e812d3bd = {funcname}()
sys.stdout.buffer.write(b'{separator}')
sys.stdout.buffer.write(pickle.dumps(de8e812d3bd))
"""

    source = re.sub(r'@(remote\.)?remotize\([^)]+\)\s*', '', source)

    lines = source.split('\n')
    indent = len(lines[0]) - len(lines[0].lstrip())
    lines = [ l[indent:] for l in lines]

    source = imports + '\n'
    source += '\n'.join(lines)
    source += wrapper

    if self.user:
      host = f'{self.user}@{self.host}'
    else:
      host = self.host
      
    command = ['ssh', '-p', f'{self.port}', ]
    if self.ssh_options:
      command += self.ssh_options.split(' ')
    command += [host, f'{python} {py_options}' if py_options else python]
  
    logging.debug('Remote, executing: {}\n{}'.format(' '.join(command), source))

    proc = subprocess.Popen(
      command,
      shell=False,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      stdin=subprocess.PIPE,
    )
  
    proc.stdin.write(source.encode(encoding))
    out, err = proc.communicate()
  
    if 0 != proc.returncode:
      if err:
        if 'Connection closed by remote host' in err.decode(encoding):
          raise RemoteConnectionRefused()
        if f'{python}: command not found' in err.decode(encoding):
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

def remotize(host, **kwargs):
  def wrap(func):
    def wrapped_f(*args):
      return Remote(host, **kwargs)(func)
    return wrapped_f
  return wrap

