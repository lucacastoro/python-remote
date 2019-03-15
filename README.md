
# Python Remote
A simple python library to execute arbitrary code on remote hosts.

## How it works
Behind the scene the `remote` library generates a Python script containing the function to execute and then it submits the script to the remote host through `ssh`.

## Usage
The idea is that you should be able to execute arbitrary Python code on a remote host transparently as if it was run on the local machine.
For example:
```
import os
from remote import remotely

host = 'remote-host'

@remotely(host, user='dev')
def get_load(index):
	return os.getloadavg()[index]

load = get_load(2)

print(f'Load avg. over the last 15 min on {host} is {load}')
```
Will execute the `get_load()` function on the **remote_host** machine as user **dev**.

Standard streams will be treated as close as possible as if the script was run locally, so doing a `print(...)` in a function wrapped in the `@remotely` decorator will cause the output to be printed on the local machine. Stdout and stderr separation is respected.

While using the `@remotely` decorator is the preferred way to use the library, it is possible to use the more basic syntax (that the decorator actually uses):
```
def foo(x):
    return x * 10

bar = Remotely(foo, host, port=22)
bar(10)  # -> 100
```
## Connecting to the remote host
Both the basic "class-based" interface and the decorator interface take a number of arguments to control the connection to the remote `ssh` server:
- `hostname` the only mandatory argument can be an IP (v4/v6) or a DNS resolvable host name.
- `port` will default to 22
- `user` when unspecified will be the name of the user running the script
- `key` is the file name of the private key to use for authenticating with the ssh server, the user's `home/.ssh` folder will be taken in account
- `compression`, defaulting to `false` eventually enables sending compressed data through the ssh protocol
- `quiet`, defaulting to false, will prevent the underlying ssh client to produce non critical warning messages
- `ssh_options` is a dictionary that can be used to pass any extra options to the ssh client as `-o`

`ssh_options` will be converted to a list of `-o key=value` entries to be passed to `ssh`. Both keys and values are strings (or at least must be objects convertible to strings), but values that are `boolean` will be treated in a specific way, converting any `True` to "yes" and any `False` to "no". So for instance the following dictionary:
```
ssh_options: { 
    'StrictHostKeyChecking': False,
    'UserKnownHostsFile': '/dev/null'
}
```
Will be sent to the underlying `ssh` command as `ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null` (if you know what I mean).

## Controlling the interpreter behavior
By default the interpreter invoked on the remote host is enforced to be the same one running on the local one, and no extra options will be given to it (for the moment), to make things a bit more flexible (but take a look at point 4 of the fore coming "Limitations" section) the following two optional arguments can be specified:

- `python`  will override the interpreter invoked on the remote host
- `py_options` as a string, will be passed to the interpreter as as a list of command line options

## Error handling
As any respectable Python library also this comes with a quite decent amount of different Exceptions:

- `RemoteConnectionRefused` will be raised whenever an `ssh` connection cannot be made
- `RemoteInterpreterMissing` will be raised when the Python interpreter needed to execute the code is not available
- `RemoteException` the most generic one, will report any not really handled issue

## Dependencies
The library does not use any non-standard library so has no "external" dependency, it relies primarily on three major libraries tho:

- `inspect` to process the source code of the functions.
- `subprocess` to execute the `ssh` invocations.
- `pickle` to serialize the Python objects between the hosts.

## Limitations
Python Remote is still under heavy development, and as for now it still has quite a few limitations:
#### 1) Avoid cross function calls
The library can only executes self-contained functions (read: it still doesn't resolves cross-functions dependencies), so doing something like:
```
def bar():
    return "world"

@remotely(...)
def foo():
    return "hello %s" % bar()
```
Will not work, resulting very likely in a `NameError`, but the following will:
```
@remotely(...)
def foo():
    def bar():
        return "world"
    return "hello %s" % bar()
```
#### 2) Avoid classes (Part I)
It is not currently possible to execute methods, but only functions, so for the moment don't even try doing something like:
```
class Foo:
    @remotely(...)
    def bar():
        ...
```
As it won't work, preliminary support for `@staticmethod` is being developed, full method support is in study as the ability to apply the decorator to a whole class (stay tuned).
#### 3) Avoid classes (Part II)
Arguments and return values can be any complex standard object (dictionaries, sets, tuples as well as int or floats for instance) but passing (or returning) classes instances is not supported yet.
#### 4) Embrace the future
Actually the library does not support Python 2.x at all so any attempt to run the library using Python 2 or to execute the remote functions on a host not provided of a Python 3.x interpreter will (miserably) fail.

---
[![Build Status](https://travis-ci.org/lucacastoro/python-remote.svg?branch=master)](https://travis-ci.org/lucacastoro/python-remote) <a href="http://www.wtfpl.net/">
