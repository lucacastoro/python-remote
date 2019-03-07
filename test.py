#!/usr/bin/python3

import remote

if __name__ == '__main__':

  def asd():
    print('hello world')

  host = 'dev11'

  try:
    remote.exec(host, asd)
  except remote.RemoteInterpreterMissing as e:
    remote.exec(host, asd, interpreter='python')
