#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, division

from schlichtanders.mycontextmanagers import until_stopped
from .mygenerators import iter_args, iter_kwargs
from itertools import izip, izip_longest, islice
from .myobjects import Namespace
from .myfunctools import fmap
from random import randint
from functools import wraps

import numpy as np  # delete again if not needed!
__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'


"""
Meta Wrappers for Optimizer Functions
#####################################

A meta wrapper takes a usual function and transforms it into another function again,
in order to support some common functionalities.

E.g. Batch version, online versions, mini batch versions of the same function can be build "higher-levelely".
But also stochastic versions, like averaging over several runs of the function.

Wrappers With One Argument
==========================
"""


def batch_sum(f):
    """ assumes args and kwargs refer to lists

    executes ``f`` on each list entry and returns summed up values
    """

    def f_batch(xs, *batch_args, **kwargs):
        # fillvalue works both as empty args and empty kwargs
        batch_args = map(iter, batch_args)

        # initialize correctly:
        summed_up = f(xs, *(next(a) for a in batch_args), **kwargs)
        with until_stopped:
            while True:
                args = [next(a) for a in batch_args]  # list is desicive! don't use generators here
                summed_up += f(xs, *args, **kwargs)
        return summed_up

    f_batch.wrapped = f
    return f_batch


def batch_mean(f):
    """ assumes args and kwargs refer to lists

    executes ``f`` on each list entry and returns summed up values
    """

    def f_batch(xs, *batch_args, **kwargs):
        # fillvalue works both as empty args and empty kwargs
        # batch_args = map(list, batch_args)
        batch_args = map(iter, batch_args)

        # initialize correctly:
        summed_up = f(xs, *(next(a) for a in batch_args), **kwargs)
        n = 1
        with until_stopped:
            while True:
                args = [next(a) for a in batch_args]  # generator use i.e. () instead of [] raises TypeError Missing rwuired input: probabilistic_target
                # TODO get to know why??
                summed_up += f(xs, *args, **kwargs)
                n += 1
        return summed_up/n

    f_batch.wrapped = f
    return f_batch

# def batch(f):
#     """ assumes args and kwargs refer to lists
#
#     executes ``f`` on each list entry and returns summed up values
#     """
#
#     def f_batch(xs, *batch_args, **batch_kwargs):
#         # fillvalue works both as empty args and empty kwargs
#         iter_args_kwargs = izip_longest(iter_args(batch_args), iter_kwargs(batch_kwargs), fillvalue={})
#
#         # initialize correctly:
#         init_args, init_kwargs = next(iter_args_kwargs)
#         summed_up = f(xs, *init_args, **init_kwargs)
#         for args, kwargs in iter_args_kwargs:
#             summed_up += f(xs, *args, **kwargs)
#         return summed_up
#
#     f_batch.wrapped = f
#     return f_batch

# def batch_mean(f):
#     """ assumes args and kwargs refer to lists
#
#     executes ``f`` on each list entry and returns summed up values
#     """
#     def f_mean(xs, *batch_args, **batch_kwargs):
#         # fillvalue works both as empty args and empty kwargs
#         batch_args = map(iter, batch_args)
#         batch_kwargs = fmap(iter, batch_kwargs)
#
#         iter_args_kwargs = izip_longest(iter_args(batch_args), iter_kwargs(batch_kwargs), fillvalue={})
#
#         # initialize correctly:
#         init_args, init_kwargs = next(iter_args_kwargs)
#         summed_up = f(xs, *init_args, **init_kwargs)
#         n = 1
#         for args, kwargs in iter_args_kwargs:
#             summed_up += f(xs, *args, **kwargs)
#             n += 1
#         return summed_up / n
#
#     f_mean.wrapped = f
#     return f_mean



def online_inf_generators(f):
    """ !!! Assumes args, kwargs to be fixed during one optimization procedure. E.g. don't use this with climin !!!

    This assumes args and kwargs to refer to infinite generators, which in principal can be called until eternity.
    Otherwise the code might simply break with a StopIteration Exception eventually
    (if the optimizer did not converged before).
    """
    outer = Namespace(
        iter_args_kwargs=None,
    )
    def f_online(xs, *batch_args, **batch_kwargs):
        # initialize args, kwargs only once:
        if outer.iter_args_kwargs is None:
            # fillvalue works both as empty args and empty kwargs
            outer.iter_args_kwargs = izip_longest(iter_args(batch_args), iter_kwargs(batch_kwargs), fillvalue={})

        next_args, next_kwargs = next(outer.iter_args_kwargs)
        return f(xs, *next_args, **next_kwargs)

    f_online.wrapped = f
    return f_online


def online(f):
    """ !!! Assumes args, kwargs to be fixed during one optimization procedure. E.g. don't use this with climin !!!
    Further like in batch, args and kwargs are assumed to refer to lists of same size (are filled with empty defaults
    if unequal sizes).
    """
    outer = Namespace(
        i=0,
        list_args_kwargs=None,
    )
    def f_online(xs, *batch_args, **batch_kwargs):
        # initialize args, kwargs only once:
        if outer.list_args_kwargs is None:
            # fillvalue works both as empty args and empty kwargs
            outer.list_args_kwargs = list(izip_longest(iter_args(batch_args), iter_kwargs(batch_kwargs), fillvalue={}))

        i = outer.i
        outer.i += 1
        if outer.i == len(outer.list_args_kwargs):
            outer.i = 0  # loop
        next_args, next_kwargs = outer.list_args_kwargs[i]
        return f(xs, *next_args, **next_kwargs)

    f_online.wrapped = f
    return f_online


def average(f, repeat_n_times=1):
    """ takes a function and returns instead an averaged version of it """
    def f_averaged(xs, *args, **kwargs):
        if repeat_n_times == 1:  # usually standard case, therefore make it a bit faster
            return f(xs, *args, **kwargs)

        # else, i.e. repeat_n_times > 1:
        summed_up = f(xs, *args, **kwargs)
        for _ in xrange(repeat_n_times - 1):
            summed_up += f(xs, *args, **kwargs)
        return summed_up / repeat_n_times

    f_averaged.wrapped = f
    return f_averaged


def chunk(f, chunk_size=20, fill=None):
    """ assumes all args, kwargs refer to same size lists """
    outer = Namespace(
        i=0,
        n_total=0,
        batch_args=None,
        batch_kwargs=None
    )

    def fill_cycle(l):
        return l.extend(l[:chunk_size])
    def fill_mirrow(l):
        return l.extend(l[-chunk_size:])
    def fill_random(l):
        return l.extend([l[randint(0, len(l)-1)] for _ in xrange(chunk_size)])
    if isinstance(fill, basestring):
        fill = locals()['fill_' + fill]

    def f_chunked(xs, *batch_args, **batch_kwargs):
        # initialize args, kwargs only once:
        if outer.batch_args is None:
            outer.batch_args = [list(b) for b in batch_args]
            outer.batch_kwargs = {k: list(v) for k,v in batch_kwargs.iteritems()}
            outer.n_total = min(len(arg) for arg in outer.batch_args + outer.batch_kwargs.values())
            if fill is not None:
                map(fill, outer.batch_args)
                fmap(fill, outer.batch_kwargs)

        a = outer.i
        outer.i += chunk_size
        b = outer.i
        if outer.i >= outer.n_total:  # todo check either args or kwargs (either might be empty)
            outer.i = 0  # loop

        return f(
            xs,
            *(arg[a:b] for arg in outer.batch_args),
            **{k: v[a:b] for k, v in outer.batch_kwargs.iteritems()}
        )
    f_chunked.wrapped = f
    return f_chunked


def chunk_inf_generators(f, chunk_size=10, fill=False):
    """ assumes all args, kwargs refer to same size lists """
    outer = Namespace(
        i=0,
        batch_args=None,
        batch_kwargs=None
    )
    if fill:
        raise ValueError("not supported yet")

    def f_chunked(xs, *batch_args, **batch_kwargs):
        # initialize args, kwargs only once:
        if outer.batch_args is None:
            # fillvalue works both as empty args and empty kwargs
            outer.batch_args = batch_args
            outer.batch_kwargs = batch_kwargs

        a = outer.i
        outer.i += chunk_size
        b = outer.i
        if outer.i >= len(outer.batch_args[0]):  # todo check either args or kwargs (either might be empty)
            outer.i = 0  # loop

        return f(
            xs,
            *(list(islice(arg, a, b)) for arg in outer.batch_args),  # TODO list call gives O(N) performance, using pure generator instead gives O(M)
            **{k: list(islice(v, a, b)) for k, v in outer.batch_kwargs.iteritems()}
        )
    f_chunked.wrapped = f
    return f_chunked


"""
Combining Wrappers
------------------

A mini-batch wrapper is as simple as combining batch with online on pre-splitted chunks of data.
    >>> mini_batch = compose(online, batch)

Read this as:
    1) (online) go over each mini-batch (i.e. list entry) separately
    2) (batch) sum up over a single mini-batch (i.e. again a list)

IMPORTANT:
    if your optimizer works in an online mode by default (like climin.util.optimizer) then of course
    mini-batch is just batch. For an optimizer with batch default (like scipy.optimize.minimize) you have to combine
    it with online like shown above.


For stochastic modeling it is often desired to average several runs. For example to compute a stochastic gradient.
For such purpose you can combine the average wrapper with the other wrappers, e.g. like so:
    >>> my_stochastic_mini_batch_wrapper = compose(mini_batch, average)

Read this as:
    1) (mini_batch) interprete the inputs as mini_batches (see above for a detailed work through)
    2) (average) instead of calculating a simple numerical value, now calculate it several times and return the averaged value instead


Applying Wrapper Kwargs
-----------------------

But how to apply the further kwarg like ``repeat_n_times``? There are different possibility which are good to know:

The explicit version::
    >>> def my_stochastic_mini_batch_wrapper(f):
    ...     return mini_batch(average(f, repeat_n_times=42)

The naive functional style version:
    >>> my_stochastic_mini_batch_wrapper = compose(mini_batch, partial(average, repeat_n_times=42))

The functional style with additional helper:
    >>> def averageN(n):
    ...     return partial(average, repeat_n_times=n)
    >>> my_stochastic_mini_batch_wrapper = compose(mini_batch, averageN(42))

Finally, using a python version of the functional style (``compose`` has the ability to pass kwargs in a clean
and save way).
    >>> my_stochastic_mini_batch_wrapper = compose(mini_batch, average)
    >>> f_wrapped = my_stochastic_mini_batch_wrapper(f, repeat_n_times=42)

The last version is probably preferrable, as the parameters can be set later dynamically from the upper level.
"""


"""
Wrappers With Several Arguments
===============================
"""


def annealing(*fs, **kwargs):
    """ linearly combines functions with given weights, where weights change over time

    :param fs: functions to be combined
    :param weights:
        keyword-argument. Referring to respective weights, how to combine functions ``fs``
        ``len(weights) == len(fs)`` must hold and weights must refer to INFINITE generators,
        as looping makes no sense at all for annealing
    """
    assert len(fs) == len(kwargs['weights'])
    iter_weights = iter_args(kwargs['weights'])

    def f_annealed(xs, *args, **kwargs):
        weights = next(iter_weights)
        return sum(w*f(xs, *args, **kwargs) for w, f in izip(weights, fs))
    f_annealed.wrapped = fs

    return f_annealed


