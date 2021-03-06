#!/usr/bin/python3

import sys

sys.path.append('..')

from execute.contained import Contained
from execute.contained import contained

image = 'python'
tag = '3'


def dock(func, *args, **kwargs):
    return Contained(func, image, tag=tag)(*args, **kwargs)


def test_void():
    def asd():
        pass
    assert(None == dock(asd))


def test_decorator():
    @contained(image, tag=tag)
    def asd():
        return 'hello'
    assert('hello' == asd())


def test_stdout(capsys):
    def asd():
        sys.stdout.write('this is stdout')
    dock(asd)
    assert(capsys.readouterr().out == 'this is stdout')


def test_stderr(capsys):
    def asd():
        sys.stderr.write('this is stderr')
    dock(asd)
    assert(capsys.readouterr().err == 'this is stderr')


def test_int():
    def asd():
        return 1
    x = dock(asd)
    assert(isinstance(x, int))
    assert(1 == x)


def test_float():
    def asd():
        return 0.5
    x = dock(asd)
    assert(isinstance(x, float))
    assert(0.5 == x)


def test_string():
    def asd():
        return 'hello'
    assert('hello' == dock(asd))


def test_tuple():
    def asd():
        return (12, 'hello')
    assert((12, 'hello') == dock(asd))


def test_list():
    def asd():
        return [12, 'hello']
    assert([12, 'hello'] == dock(asd))


def test_dict():
    def asd():
        return {'hello': 12}
    assert({'hello': 12} == dock(asd))


def test_arg1():
    def asd(y):
        return "Hello " + y
    x = dock(asd, 'world')
    assert(x == 'Hello world')


def test_arg2():
    def asd(x, y):
        return x + ' ' + y
    assert('hello world' == dock(asd, 'hello', 'world'))


def test_nested():
    def outer(x):
        def inner(y):
            return y * 2
        return [inner(z) for z in x]
    assert([2, 4, 6] == dock(outer, [1, 2, 3]))
