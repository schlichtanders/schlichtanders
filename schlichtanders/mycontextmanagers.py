#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Simply but highly useful context managers.
"""
from __future__ import division
import contextlib

__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'


@contextlib.contextmanager
def ignored(*exceptions):
    """ silently ignores exceptions when raised """
    try:
        yield
    except exceptions:
        pass


class UntilStopped(object):
    """ same as ``ignored`` only specific for StopIteration """
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type == StopIteration:
            return True
        return False

until_stopped = UntilStopped()
