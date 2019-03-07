#!/usr/bin/python3

import remote, logging

#logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':

  def asd():
    print('hello world')
    return 'culo!'

  host = 'dev11'

  try:
    print(remote.exec(host, asd))
  except remote.RemoteInterpreterMissing as e:
    print(remote.exec(host, asd, interpreter='python'))
