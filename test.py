#!/usr/bin/python3

import sys, remote, logging, types, unittest

#logging.basicConfig(level=logging.DEBUG)

# ssh -i key -o StrictHostKeyChecking=no -p 2222 test@localhost

if __name__ == '__main__':
    
  user = 'test'
  host = 'localhost'
  port = 2222
  hostname = 'test'
  ssh_opts = '-i ssh-key -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'

  def rem(host, func):
    return remote.Remote(host, user=user, port=port, ssh_options=ssh_opts)(func)

  class Tests(unittest.TestCase):

    def test_stdout(self):
      def asd():
        sys.stdout.write('this is stdout\n')
      rem(host, asd)
    
    def test_stderr(self):
      def asd():
        sys.stderr.write('this is stderr\n')
      rem(host, asd)
  
    def test_void(self):
      def asd():
        pass
      assert None == rem(host, asd)
    
    def test_int(self):
      def asd():
        return 1
      x = rem(host, asd)
      assert isinstance(x, int)
      assert 1 == x
    
    def test_float(self):
      def asd():
        return 0.5
      x = rem(host, asd)
      assert isinstance(x, float)
      assert 0.5 == x
    
    def test_string(self):
      def asd():
        return 'hello'
      assert 'hello' == rem(host, asd)

    def test_tuple(self):
      def asd():
        return (12, 'hello')
      assert (12, 'hello') == rem(host, asd)

    def test_list(self):
      def asd():
        return [12, 'hello']
      assert [12, 'hello'] == rem(host, asd)

    def test_dict(self):
      def asd():
        return {'hello': 12}
      assert {'hello': 12} == rem(host, asd)

    def test_decorator(self):
      @remote.remotize(host, port=port, user=user, ssh_options=ssh_opts)
      def asd():
        return 'hello'
      assert 'hello' == asd()

    def test_hostname(self):
      def asd():
        return subprocess.check_output('hostname').decode('utf-8').rstrip()
      x = rem(host, asd)
      assert x == hostname

  unittest.main()
