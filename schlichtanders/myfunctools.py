#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
import inspect
import numpy as np
from types import FunctionType, GeneratorType
from functools import wraps, partial
from collections import Mapping, Sequence
from itertools import izip, count
from mygenerators import iter_args, iter_kwargs
from schlichtanders.mycontextmanagers import until_stopped

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
convert
=======
as analog to fmap (see below) for type conversions
"""


def convert(obj, type):
    for (obj_type, conversion_type), conversion in convertible.iteritems():
        if issubclass(conversion_type, type) and isinstance(obj, obj_type):
            if not isinstance(obj, type):
                return conversion(obj)
            return obj
    raise ValueError("cannot convert %s to type %s" % (obj, type))


def convert_to_list(obj):
    if obj is None:
        return []
    return [obj]

convertible = {
    # should be sorted such that most general come first
    (object, list): convert_to_list
}


"""
map reduce fmaps
----------------

They are mainly useful for working with numeric return types and hence not that general as the functions here.
Still they fit well enough.
"""


def summap(f, *batch_args):
    """ assumes args and kwargs refer to lists

    executes ``f`` on each list entry and returns summed up values
    """
    batch_args = map(iter, batch_args)
    # initialize correctly:
    try:
        summed_up = f(*[next(a) for a in batch_args])  # [] are essential as StopIteration is not handled intuitively
    except StopIteration:
        raise ValueError("empty args")
    with until_stopped:
        while True:
            summed_up += f(*[next(a) for a in batch_args])
    return summed_up


def meanmap(f, *batch_args):
    """ assumes args and kwargs refer to lists

    executes ``f`` on each list entry and returns summed up values
    """
    batch_args = map(iter, batch_args)

    # initialize correctly:
    try:
        summed_up = f(*[next(a) for a in batch_args])
    except StopIteration:
        raise ValueError("empty args")
    n = 1
    with until_stopped:
        while True:
            # TODO get to know why??
            summed_up += f(*[next(a) for a in batch_args])
            n += 1
    return summed_up/n


class SimulateOnline(object):
    """ regards args as iterators where f is executed on each separately, consecutively"""
    @staticmethod
    def hash_by_id(all_args):
        return tuple(id(a) for a in all_args)

    @staticmethod
    def hash_by_hash(all_args):
        return hash(all_args)

    def __init__(self, cycle=True, hash_by=lambda all_args: None):
        """ defaults to cycling and one unique hash

        if you want to reuse an SomulateOnline instance for several inputs,
        think about using ``SimulateOnline.hash_by_id`` or ``SimulateOnline.hash_by_hash``
        instead of the default ``hash_by``
        """
        self.original_args = {}
        self.iter_args = {}
        self.cycle = cycle
        self.hash_by = hash_by

    def __call__(self, f, *all_args):
        key = self.hash_by(all_args)
        while True:  # for retrying
            try:
                return f(*[next(a) for a in self.iter_args[key]])
            except StopIteration as e:
                # if not infinite, reinitalize iterator
                if self.cycle:
                    self.iter_args[key] = map(iter, self.original_args[key])
                else:
                    raise e
            except KeyError:
                # fillvalue works both as empty args and empty kwargs
                self.original_args[key] = all_args
                self.iter_args[key] = map(iter, all_args)


class Average(object):
    """ computes result several times and returns averages of all """
    def __init__(self, repeat_n_times=1):
        self.repeat_n_times = repeat_n_times

    def __call__(self, f, *args):
        if self.repeat_n_times == 1:  # usually standard case, therefore make it a bit faster
            return f(*args)
        # else, i.e. repeat_n_times > 1:
        summed_up = f(*args)
        for _ in xrange(self.repeat_n_times - 1):
            summed_up += f(*args)
        return summed_up / self.repeat_n_times


def sumexp(values):
    largest = reduce(np.maximum, values)
    return largest + np.log(sum(np.exp(r - largest) for r in values))


def meanexp(values):
    return sumexp(values) - np.log(len(values))


def meanexpmap(f, *batch_args):
    """ numerical stable version of log(1/n*sum(exp(...)) """
    values = [f(*args) for args in izip(*batch_args)]
    return meanexp(values)


class AverageExp(object):
    """ like average, only that the average is computed on exponential scale

    log(Average(exp(x)))"""
    def __init__(self, repeat_n_times=1, numerical_stable=True):
        self.repeat_n_times = repeat_n_times
        self.numerical_stable = numerical_stable

    def __call__(self, f, *args):
        if self.repeat_n_times == 1:  # usually standard case, therefore make it a bit faster
            return f(*args)
        # else, i.e. repeat_n_times > 1:
        if self.numerical_stable:
            repetitions = [f(*args) for _ in xrange(self.repeat_n_times)]
            return meanexp(repetitions)
        else:
            summed_up = np.exp(f(*args))
            for _ in xrange(self.repeat_n_times - 1):
                summed_up += np.exp(f(*args))
            return np.log(summed_up) - np.log(self.repeat_n_times)




"""
fmap/lift
---------
"""


def fmap(func, *contexts, **kwargs_contexts):
    """generic map interface to lift a function to be able to work with different containers / contexts

    Instead of a normal call ``func(*args, **kwargs)`` use ``fmap(func, *args, **kwargs)`` to work natively
    on more abstract containers.

    Support for lists, generators, tuples (everything map supports), functions,
    and generally classes which implement "__map__" are listed in ``fmappable``.

    Parameters
    ----------
    func : function
        to be mapped
    contexts : list of same type
        to be mapped upon
    kwargs_contexts : kwargs
        to be mapped upon
    _inplace : bool, defaults to False
        kwarg which will be popped from func_kwargs, indicating whether the function shall be mapped in place (if possible)
        Note, that for this func must return the same number of outputs as contexts

    Returns
    -------
    mapped result
    """
    inplace = kwargs_contexts.pop('_inplace', False)
    if len(contexts) == 1 and len(kwargs_contexts) == 0 and hasattr(contexts[0], '__map__'):
        return contexts[0].__map__(func, inplace=inplace)

    for klass in fmappable:
        if all(isinstance(con, klass) for con in contexts + tuple(kwargs_contexts.itervalues())):
            ret = fmappable[klass](func, *contexts, _inplace=inplace, **kwargs_contexts)
            if inplace:
                return contexts[0] if len(contexts) == 1 else None
            else:
                return ret
    else:
        # final default: just apply function to values, this makes fmap interface very easy, but also probably difficult to debug
        if inplace:
            raise ValueError("Cannot fmap inplace on singletons.")
        return func(*contexts)


def fmap_function(func, *contexts, **kwargs_contexts):
    """ fmap implementation to work with functions """
    if kwargs_contexts.pop('_inplace', False):
        raise ValueError("Cannot fmap inplace on functions.")

    @wraps(contexts[0])  # TODO improve this? by combining signatures - similar to compose
    def generic_func(*args, **kwargs):
        return func(*(use_as_needed(con, kwargs, args=args) for con in contexts),
                    **{k: use_as_needed(con, kwargs, args=args) for k, con in kwargs_contexts})
    generic_func.contexts = contexts
    return generic_func


def fmap_dict(func, *contexts, **kwargs_contexts):
    """ fmap implementation to work with dicts (more general Mapping)

    inplace only affects *contexts"""
    inplace = kwargs_contexts.pop('_inplace', False)
    newdict = {}
    for key in contexts[0].keys():
        try:
            newdict[key] = func(*(con[key] for con in contexts),
                                **{k: con[key] for k, con in kwargs_contexts})
        except KeyError:
            continue
    if not inplace:
        return newdict
    else:
        for k, vs in newdict.iteritems():
            for c, v in izip(contexts, vs):
                c[k] = v


def fmap_iterable(func, *contexts, **kwargs_contexts):
    """ inplace works only for Mutable types and will effect only contexts """
    inplace = kwargs_contexts.pop('_inplace', False)
    iter_contexts = [iter(c) for c in contexts]
    kwargs_iter_contexts = {k: iter(c) for k, c in kwargs_contexts.iteritems()}
    try:
        for i in count(0):
            ret = func(*(next(con) for con in iter_contexts),
                       **{k: next(con) for k, con in kwargs_iter_contexts.iteritems()})
            if not inplace:
                yield ret
            else:
                for c, r in izip(contexts, ret):
                    c[i] = r
    except StopIteration:
        pass


def fmap_list(func, *contexts, **kwargs_contexts):
    """ fmap implementation to work with lists (more general Sequence) """
    ret = list(fmap_iterable(func, *contexts, **kwargs_contexts))
    return ret if ret else None  # list of empty generator is [] not None


fmappable = {
    FunctionType: fmap_function,
    Mapping: fmap_dict,
    GeneratorType: fmap_iterable,
    Sequence: fmap_list,
}


def lift(f, *fmaps):
    """ will transform func to a new function with the fmaps applied like function composition
    e.g.
    >>> f_lifted = lift(f, summap, Average(10))
    will kind of first execute f, then summap on f, and then Average over summap finally. From inner towards outer.

    If no fmaps are given, the general fmap is used

    lift is kind of function composition for fmaps, only without fancy kwargs support
    """
    fmaps = [fmap] if not fmaps else fmaps  # revert everything as we thinking in terms of function composition
    def single_lift(f, fmap):
        return partial(fmap, f)
    f_lifted = reduce(single_lift, fmaps, f)
    f_lifted.wrapped = f
    return f_lifted


def compose_fmap(*fmaps):
    """ internally like lift, only that it returns a fmap
    CAUTION: order is exactly reversed compared to lift (because of compose analogy)"""
    final_fmap = fmaps[0]
    def overall_fmap(f, *args):
        inner_f = lift(f, *fmaps[-1:0:-1])  # 0 is not included
        return final_fmap(inner_f, *args)
    return overall_fmap


def as_wrapper(*fmaps, **kwargs):
    """ transforms fmap/fmaps into a wrapper function which can be applied to a function

    again a version of lift

    Parameters
    ----------
    reverse : bool
        if True (default), function composition order is used (like compose_fmap), else order like used in lift
    """
    if kwargs.pop('reverse', True):
        fmaps = fmaps[::-1]  # function composition style
    def wrapper(f):
        return lift(f, *fmaps)
    return wrapper


"""
function composition
--------------------
"""

# # http://stackoverflow.com/questions/1409295/set-function-signature-in-python
# # changing signature for compose (does not work for Compose). Use the following pattern:
# argstr = ", ".join(arglist)
# fakefunc = "def func(%s):\n    return real_func(%s)\n" % (argstr, argstr)
# fakefunc_code = compile(fakefunc, "fakesource", "exec")
# fakeglobals = {}
# eval(fakefunc_code, {"real_func": f}, fakeglobals)
# f_with_good_sig = fakeglobals["func"]
#
# help(f)               # f(*args, **kwargs)
# help(f_with_good_sig) # func(foo, bar, baz)


def identity(x):
    return x


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
    funcs = [f for f in funcs if f != identity]
    if not funcs:
        funcs = [identity]

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
        if len(funcs) == 1 and isinstance(funcs[0], list):  # regarded single list of funcs as funcs itself
            self.funcs = funcs[0]
        else:
            self.funcs = list(funcs)

    def __call__(self, *args, **kwargs):
        """
        calls the composed functions

        Parameters
        ----------
        args
            args for very first function. Next function's args is previous function's output.
        kwargs
            kwargs for ALL functions. Will only get called with what is available

        Returns
        -------
        output of very last function
        """
        return compose(*self.funcs, expand_tuple=self.expand_tuple)(*args, **kwargs)

    def __iadd__(self, other):
        if isinstance(other, Compose):
            self.funcs += other.funcs
        else:  # check function instance?
            self.funcs.append(other)
        return self

    def __add__(self, other):
        if isinstance(other, Compose):
            return Compose(self.funcs + other.funcs)
        else: #check function instance?
            return Compose(self.funcs + [other])

    def __radd__(self, lother):
        if isinstance(lother, Compose):
            return Compose(lother.funcs + self.funcs)
        else:  # check function instance?
            return Compose([lother] + self.funcs)

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