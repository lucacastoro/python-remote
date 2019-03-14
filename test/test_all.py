#!/usr/bin/python3

import sys, os, io, remote, logging, types, unittest
from remote import remotely
import netifaces

# logging.basicConfig(level=logging.DEBUG)

def get_address():
    return '172.17.0.1'
    iface = [i for i in netifaces.interfaces() if i != 'lo'][0]
    return netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']

hostname = 'test-server'
user = 'test'
host = os.environ['TEST_SERVER'] or 'localhost' 
port = 2222
pkey = './ssh-key'
opts = {
    'StrictHostKeyChecking': False,
    'UserKnownHostsFile': '/dev/null'
}


def rem(host, func, *args, **kwargs):
    return remote.Remote(func, host, user=user, port=port, key=pkey, ssh_options=opts)(*args, **kwargs)


def test_stdout(capsys):
    def asd():
        sys.stdout.write('this is stdout')
    rem(host, asd)
    assert(capsys.readouterr().out == 'this is stdout')


def test_stderr(capsys):
    def asd():
        sys.stderr.write('this is stderr')
    rem(host, asd)
    assert(capsys.readouterr().err == 'this is stderr')


def test_void():
    def asd():
        pass
    assert(None == rem(host, asd))


def test_int():
    def asd():
        return 1
    x = rem(host, asd)
    assert(isinstance(x, int))
    assert(1 == x)


def test_float():
    def asd():
        return 0.5
    x = rem(host, asd)
    assert(isinstance(x, float))
    assert(0.5 == x)


def test_string():
    def asd():
        return 'hello'
    assert('hello' == rem(host, asd))


def test_tuple():
    def asd():
        return (12, 'hello')
    assert((12, 'hello') == rem(host, asd))


def test_list():
    def asd():
        return [12, 'hello']
    assert([12, 'hello'] == rem(host, asd))


def test_dict():
    def asd():
        return {'hello': 12}
    assert({'hello': 12} == rem(host, asd))


def test_decorator():
    @remote.remotely(host, port=port, user=user, key=pkey, ssh_options=opts)
    def asd():
        return 'hello'
    assert('hello' == asd())


def test_hostname():
    def asd():
        return subprocess.check_output('hostname').decode('utf-8').rstrip()
    x = rem(host, asd)
    assert(x == hostname)


def test_arg1():
    def asd(y):
        return "Hello " + y
    x = rem(host, asd, 'world')
    assert(x == 'Hello world')


def test_arg2():
    @remotely(host, port=port, user=user, key=pkey, ssh_options=opts)
    def asd(x):
        return 'hello ' + x
    assert('hello world' == asd('world'))

