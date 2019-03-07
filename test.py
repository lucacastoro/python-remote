#!/usr/bin/python3

import remote, logging

#logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':

  def asd():
    sys.stdout.write('this is stdout\n')
    sys.stderr.write('this is stderr\n')
    return 'culo!'

  host = 'dev11'

  try:
    print(remote.exec(host, asd))
  except remote.RemoteInterpreterMissing as e:
    print(remote.exec(host, asd, interpreter='python'))
