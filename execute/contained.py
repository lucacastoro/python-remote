#!/usr/bin/python3

import os, sys, re, subprocess, logging
from functools import wraps
from .executor import Executor

class ContainerException(Exception):

    def __init__(self, name):
        super().__init__(name)

class Contained(Executor):

    def __init__(self, func, image, tag='latest', python=None, py_options=None):
        super().__init__(func, python, py_options, ['contained.contained'])
        self.image = image
        self.tag = tag
        pass

    def _execute(self, script):

        python = self.python or 'python3'
        if self.py_options:
            python += ' ' + self.py_options
        local_script = '/tmp/asdasdasd.py'
        remote_script = local_script

        command = [
            'docker', 'run', '-i', '--rm',
            "{image}:{tag}".format(image=self.image, tag=self.tag),
            python
        ]

        with subprocess.Popen(
            command,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
        ) as proc:
            out, err = proc.communicate(script.encode('utf-8'))
            return proc.returncode, out, err

    def _fail(self, err):
        raise ContainerException(err)


def contained(*ext_args, **ext_kwargs):
    def wrap(func):
        def wrapped_f(*args, **kwargs):
            return Contained(func, *ext_args, **ext_kwargs)(*args, **kwargs)
        return wrapped_f
    return wrap

