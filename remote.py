#!/usr/bin/python3

import os, sys, re, inspect, subprocess, types, logging, pickle

class RemoteException(Exception):
  def __init__(self, name):
    super().__init__(name)


class RemoteInterpreterMissing(RemoteException):
  __slots__ = ('interpreter')
  def __init__(self, name):
    self.interpreter = name
    super().__init__(f'missing remote interpreter: {name}')


def exec(host, func, interpreter=None, options='', transport='ssh'):
  
  if not interpreter:
    interpreter = os.path.basename(sys.executable)

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
xxx = {funcname}()
sys.stdout.write('{separator}')
sys.stdout.write(pickle.dumps(xxx))
"""

  lines = source.split('\n')
  indent = len(lines[0]) - len(lines[0].lstrip())
  lines = [ l[indent:] for l in lines]

  source = imports + '\n'
  source += '\n'.join(lines)
  source += wrapper

  command = [transport, host, f'{interpreter} {options}']

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
      if re.search(f'{interpreter}: command not found', err.decode(encoding)):
        raise RemoteInterpreterMissing(interpreter)
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
    ret = pickle.loads(ret)

  return ret
