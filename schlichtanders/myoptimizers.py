#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, division
from .mygenerators import iter_args, iter_kwargs
from itertools import izip, izip_longest
from .myobjects import Namespace

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


def batch(f):
    """ assumes args and kwargs refer to lists

    executes ``f`` on each list entry and returns summed up values
    """
    def f_batch(xs, *batch_args, **batch_kwargs):
        # fillvalue works both as empty args and empty kwargs
        iter_args_kwargs = izip_longest(iter_args(batch_args), iter_kwargs(batch_kwargs), fillvalue={})

        # initialize correctly:
        init_args, init_kwargs = next(iter_args_kwargs)
        summed_up = f(xs, *init_args, **init_kwargs)
        for args, kwargs in iter_args_kwargs:
            summed_up += f(xs, *args, **kwargs)
        return summed_up

    return f_batch


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

    return f_averaged



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

    return f_annealed


