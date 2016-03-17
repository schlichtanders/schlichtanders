#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, division

__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'

def compose(*funcs, **kwargs):
    """ simple generic compose function for functions

    :param funcs: functions to be concatinated. By default (func1, func2, func3) -> func1(func2(func3(...))).
    :param kwargs:
        "firstlatest" (default True)
            ===== =================================================
            Value Effect
            ===== =================================================
            True  (func1, func2, func3) -> func1(func2(func3(...)))
            False (func1, func2, func3) -> func3(func2(func1(...)))
            ===== =================================================
    :return: concatinated functions
    """
    firstlatest = kwargs.get("firstlatest", True) #: python 2.7 workaround for keywords after *args
    if firstlatest:
        funcs = funcs[::-1]

    def call(args, f):
        if isinstance(args, tuple):
            return f(*args)
        else:
            return f(args)

    def composed(*args):
        return reduce(call, funcs, args)
    return composed