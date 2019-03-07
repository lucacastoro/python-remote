#!/usr/bin/python3

import os, sys, re, inspect, subprocess, random, types

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
  name = func.__name__
  modules = (val.__name__ for name, val in globals().items() if isinstance(val, types.ModuleType))
  imports = ''
  source = inspect.getsource(func)
  filename = '/tmp/{}.py'.format(name)

  for module in modules:
    imports += f"""
try:
  import {module}
except:
  pass
    """

  lines = source.split('\n')
  indent = len(lines[0]) - len(lines[0].lstrip())
  lines = [ l[indent:] for l in lines]

  source = imports + '\n'
  source += '\n'.join(lines)
  source += f'\n{name}()'
  source = source.encode('ascii')

  proc = subprocess.Popen(
    [transport, host, f'{interpreter} {options}'],
    shell=False,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    stdin=subprocess.PIPE,
  )

  proc.stdin.write(source)
  out, err = proc.communicate()

  if err:
    if re.search(f'{interpreter}: command not found', err.decode('utf-8')):
      raise RemoteInterpreterMissing(interpreter)
    raise RemoteException(err)

  if 0 != proc.returncode:
    raise RemoteException('remote execution failed')

  if out:
      print(out.decode('utf-8')[:-1])
