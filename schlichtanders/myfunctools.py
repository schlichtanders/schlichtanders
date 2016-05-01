#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, division
import inspect
from types import FunctionType
from functools import wraps, partial

__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'

"""
general
-------
"""
def use_as_needed(func, kwargs, args=tuple()):
    meta = inspect.getargspec(func)
    if meta.keywords is not None:
            return func(*args, **kwargs)
    else:
        # not generic super-constructor - pick only the relevant subentries:
        return func(*args, **{k:kwargs[k] for k in kwargs if k in meta.args[len(args):]})


"""
fmap
----
"""

def fmap(func, *contexts, **func_kwargs):
    """ generic map interface to lift a function to be able to work with different containers / contexts

    Instead of a normal call ``func(arg, **kwargs)`` use ``fmap(func, arg, **kwargs)`` to work natively
    on more abstract containers.

    Support for lists, generators, tuples (everything map supports), functions,
    and generally classes which implement "__map__" are listed in ``fmappable``.
    """
    func = partial(func, **func_kwargs)
    if len(contexts) == 1 and hasattr(contexts[0], '__map__'):
        return contexts[0].__map__(func)

    elif contexts[0].__class__ in fmappable and all(contexts[0].__class__ == con.__class__ for con in contexts[1:]):
        return fmappable[contexts[0].__class__](func, *contexts)

    else:
        return map(func, *contexts)

def fmap_function(func, *contexts):
    """ fmap implementation to work with functions """
    @wraps(contexts[0])  # TODO improve this? by combining signatures - similar to compose
    def generic_func(*args, **kwargs):
        return func(*(use_as_needed(con, kwargs, args=args) for con in contexts))

    return generic_func

fmappable = {
    FunctionType: fmap_function
}



"""
compose
-------
"""

def compose(*funcs, **kwargs):
    """ Higher level function to compose several functions

    The composed function supports passing of kwarks arguments, where each function gets only those args, which an
    inspect on the function signature revealed.

    :param funcs: functions to be concatinated. By default (func1, func2, func3) -> func1(func2(func3(...))).
    :param firstlatest: (default True)
        ===== =================================================
        Value Effect
        ===== =================================================
        True  (func1, func2, func3) -> func1(func2(func3(...)))
        False (func1, func2, func3) -> func3(func2(func1(...)))
        ===== =================================================

    :param expand_tuple: (default True)
        If True expand a return value of type tuple, so that next function is called like ``f(*tuple)``

    :return: concatinated functions
    """
    firstlatest = kwargs.get("firstlatest", True)  #: python 2.7 workaround for keywords after *args
    expand_tuple = kwargs.get("expand_tuple", True)  #: python 2.7 workaround for keywords after *args
    funcs = funcs[::-1] if firstlatest else funcs

    def composed(*args, **kwargs):  # TODO build a useful function documentation like usual for function wrappers
        def call(args, f):
            """ call which also passes kwargs arguments """
            if expand_tuple and isinstance(args, tuple):  # i.e. expand *args
                return use_as_needed(f, kwargs, args=args)
            else:
                return use_as_needed(f, kwargs, args=[args])
        return reduce(call, funcs, args)

    return composed


class Compose(object):
    """ this is class for the compose method

    It overwrites + operator and (experimental) also . operator for function concatination.
    As this of course works only with objects of type Compose, one way to use the concatination syntax
    is to start with the trivial function lambda x:x which is also available as a Compose, named "I".

    Hence
        composed_func = I + func1 + func2
        composed_func = I . func1 . func2
        composed_func = lambda *args, **kwargs: func1(func2(*args, **kwargs))

    are essentially the same, only that they support better kwargs passing throughout the chain of functions.

    The . syntax might not be recommandable as this might confuse others. It is not meant as an operator (the operator
    functionality uses python's frame hack). At least use it with spaces inbetween, so that it looks more like an operator.
    """

    def __init__(self, *funcs, **kwargs):
        """ Generic Compose class for functions. Use it as if this would be a higher level function.

        :param funcs: functions to be concatinated. (func1, func2, func3) -> func1(func2(func3(...))).
        :param expand_tuple: (default True)
            If True expand a return value of type tuple, so that next function is called like ``f(*tuple)``

        :return: concatinated functions
        """
        self.expand_tuple = kwargs.get("expand_tuple", True)  #: python 2.7 workaround for keywords after *args
        if len(funcs) == 1 and isinstance(funcs[0], list): # regarded single list of funcs as funcs itself
            funcs = funcs[0]
        else:
            funcs = list(funcs)
        self._funcs = funcs[::-1] # as the last one has to be called first

    def __call__(self, *args, **kwargs):
        return compose(self._funcs, expand_tuple=self.expand_tuple)(*args, **kwargs)

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