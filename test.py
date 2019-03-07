#!/usr/bin/python3

import remote, logging, types, unittest

#logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    
  host = 'dev11'
  
  def rem(host, what):
      return remote.remotely(host, what, interpreter=[None, 'python'])

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
      assert isinstance(rem(host, asd), int)
    
    def test_float(self):
      def asd():
        return 0.5
      assert isinstance(rem(host, asd), float)
    
    def test_string(self):
      def asd():
        return "hello"
      ret = rem(host, asd)
      assert isinstance(ret, str)
      assert ret == "hello"

    def test_tuple(self):
      def asd():
        return (12, "hello")
      x = rem(host, asd)
      assert x == (12, "hello") 

    def test_list(self):
      def asd():
        return [12, "hello"]
      x = rem(host, asd)
      assert x == [12, "hello"]

    def test_dict(self):
      def asd():
          return {"hello": 12}
      x = rem(host, asd)
      assert x == {"hello": 12}

    def test_decorator(self):
      @remote.remotize(host, interpreter=[None, 'python'])
      def asd():
        return "hello"
      ret = asd()
      assert isinstance(ret, str)
      assert ret == "hello"
  unittest.main()
