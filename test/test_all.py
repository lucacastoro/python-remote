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


def test_decorator():
    @remote.remotely(host, port=port, user=user, key=pkey, ssh_options=opts)
    def asd():
        return 'hello'
    assert('hello' == asd())


def rem(func, *args, **kwargs):
    return remote.Remote(func, host, user=user, port=port, key=pkey, ssh_options=opts)(*args, **kwargs)


def test_stdout(capsys):
    def asd():
        sys.stdout.write('this is stdout')
    rem(asd)
    assert(capsys.readouterr().out == 'this is stdout')


def test_stderr(capsys):
    def asd():
        sys.stderr.write('this is stderr')
    rem(asd)
    assert(capsys.readouterr().err == 'this is stderr')


def test_void():
    def asd():
        pass
    assert(None == rem(asd))


def test_int():
    def asd():
        return 1
    x = rem(asd)
    assert(isinstance(x, int))
    assert(1 == x)


def test_float():
    def asd():
        return 0.5
    x = rem(asd)
    assert(isinstance(x, float))
    assert(0.5 == x)


def test_string():
    def asd():
        return 'hello'
    assert('hello' == rem(asd))


def test_tuple():
    def asd():
        return (12, 'hello')
    assert((12, 'hello') == rem(asd))


def test_list():
    def asd():
        return [12, 'hello']
    assert([12, 'hello'] == rem(asd))


def test_dict():
    def asd():
        return {'hello': 12}
    assert({'hello': 12} == rem(asd))


def test_hostname():
    def asd():
        return subprocess.check_output('hostname').decode('utf-8').rstrip()
    x = rem(asd)
    assert(x == hostname)


def test_arg1():
    def asd(y):
        return "Hello " + y
    x = rem(asd, 'world')
    assert(x == 'Hello world')


def test_arg2():
    def asd(x, y):
        return x + ' ' + y
    assert('hello world' == rem(asd, 'hello', 'world'))


def test_nested():
    def outer(x):
        def inner(y):
            return y * 2
        return [inner(z) for z in x]
    assert([2, 4, 6] == rem(outer, [1, 2, 3]))


def test_load():
    def load_avarage():
    	return os.getloadavg()

    assert(len(rem(load_avarage)) == 3)


def test_user():
    def get_user():
        return os.getlogin()
    assert(rem(get_user) == user)