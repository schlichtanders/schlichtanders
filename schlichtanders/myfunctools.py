#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, division
import inspect

__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'

def use_as_needed(func, kwargs):
    meta = inspect.getargspec(func)
    if meta.keywords is not None:
            return func(**kwargs)
    else:
        # not generic super-constructor - pick only the relevant subentries:
        return func(**{k:kwargs[k] for k in kwargs if k in meta.args})


def call(args, f):
    if isinstance(args, tuple):
        return f(*args)
    else:
        return f(args)


# ----------------------


class Compose(object):

    #: global setting of firstlatest
    FIRSTLATEST = True

    def __init__(self, *funcs, **kwargs):
        """ Generic Compose class for functions. Use it as if this would be a higher level function.

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
        if len(funcs) == 1 and isinstance(funcs[0], list): # regarded single list of funcs as funcs itself
            funcs = funcs[0]
        else:
            funcs = list(funcs)
        firstlatest = kwargs.get("firstlatest", Compose.FIRSTLATEST)  #: python 2.7 workaround for keywords after *args
        self._funcs = funcs[::-1] if firstlatest else funcs

    def __call__(self, *args, **kwargs):
        def call(args, f):
            """ call which also passes kwargs arguments """
            meta = inspect.getargspec(f)
            if isinstance(args, tuple):  #i.e. expand *args
                if meta.keywords is not None:
                    return f(*args, **kwargs)
                else:
                    # no generic kwargs parameter - pick only the relevant (left) subentries:
                    return f(*args, **{k: kwargs[k] for k in kwargs if k in meta.args[len(args):]})
            else:
                if meta.keywords is not None:
                    return f(args, **kwargs)
                else:
                    # no generic kwargs parameter - pick only the relevant (left) subentries:
                    return f(args, **{k: kwargs[k] for k in kwargs if k in meta.args[1:]})
        return reduce(call, self._funcs, args)

    def __iadd__(self, other):
        if isinstance(other, Compose):
            self._funcs += other._funcs
        else:  # check function instance?
            self._funcs.append(other)
        return self

    def __add__(self, other):
        if isinstance(other, Compose):
            return Compose(self._funcs + other._funcs)
        else: #check function instance?
            return Compose(self._funcs + [other])

    def __radd__(self, lother):
        if isinstance(lother, Compose):
            return Compose(lother._funcs + self._funcs)
        else:  # check function instance?
            return Compose([lother] + self._funcs)

    def __getattr__(self, name):
        """ overwriting . to work as +
        Intended use::

            composed_function = I . func1 . func2 . func2  # = lambda *args, **kwargs : func1(func2(func3(*args, **kwargs))

        Note:: you cannot use this with function names "_func" and "FIRSTLATEST", as they are attributes of Compose
        Note:: this does not work "from the right", i.e. the left object must be of instance Compose
        """
        frame = inspect.currentframe()
        func = frame.f_back.f_locals[name]
        del frame
        return self + func

I = Compose()