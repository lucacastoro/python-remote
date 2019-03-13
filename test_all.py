#!/usr/bin/python3

import sys, os, io, remote, logging, types, unittest
from remote import remotely
import pytest

# logging.basicConfig(level=logging.DEBUG)

hostname = 'test'
user = 'test'
host = 'localhost'
port = 2222
pkey = './ssh-key'
opts = {
    'StrictHostKeyChecking': False,
    'UserKnownHostsFile': '/dev/null'
}


def rem(host, func, *args, **kwargs):
    return remote.Remote(func, host, user=user, port=port, key=pkey, ssh_options=opts)(*args, **kwargs)


class All(unittest.TestCase):

    # https://github.com/pytest-dev/pytest/issues/2504
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def test_stdout(self):
        def asd():
            sys.stdout.write('this is stdout')
        rem(host, asd)
        self.assertEqual(self.capsys.readouterr().out, 'this is stdout')

    def test_stderr(self):
        def asd():
            sys.stderr.write('this is stderr')
        rem(host, asd)
        self.assertEqual(self.capsys.readouterr().err, 'this is stderr')

    def test_void(self):
        def asd():
            pass
        self.assertEqual(None, rem(host, asd))
    
    def test_int(self):
        def asd():
            return 1
        x = rem(host, asd)
        self.assertTrue(isinstance(x, int))
        self.assertEqual(1, x)
    
    def test_float(self):
        def asd():
            return 0.5
        x = rem(host, asd)
        self.assertTrue(isinstance(x, float))
        self.assertEqual(0.5, x)
    
    def test_string(self):
        def asd():
            return 'hello'
        self.assertEqual('hello', rem(host, asd))

    def test_tuple(self):
        def asd():
            return (12, 'hello')
        self.assertEqual((12, 'hello'), rem(host, asd))

    def test_list(self):
        def asd():
            return [12, 'hello']
        self.assertEqual([12, 'hello'], rem(host, asd))

    def test_dict(self):
        def asd():
            return {'hello': 12}
        self.assertEqual({'hello': 12}, rem(host, asd))

    def test_decorator(self):
        @remote.remotely(host, port=port, user=user, key=pkey, ssh_options=opts)
        def asd():
            return 'hello'
        self.assertEqual('hello', asd())

    def test_hostname(self):
        def asd():
            return subprocess.check_output('hostname').decode('utf-8').rstrip()
        x = rem(host, asd)
        self.assertEqual(x, hostname)

    def test_arg1(self):
        def asd(y):
            return "Hello " + y
        x = rem(host, asd, 'world')
        self.assertEqual(x, 'Hello world')
    
    def test_arg2(self):
        @remotely(host, port=port, user=user, key=pkey, ssh_options=opts)
        def asd(x):
            return 'hello ' + x
        self.assertEqual('hello world', asd('world'))

