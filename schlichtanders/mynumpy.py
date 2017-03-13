#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Addition to myarrays. They should merged I think."""

from __future__ import print_function, division
import numpy
import numpy as np
import mygenerators
__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'

import numpy as np
from itertools import chain
izip = zip


def find(a, predicate, chunk_size=1024):
    """
    Find the indices of array elements that match the predicate.

    Parameters
    ----------
    a : array_like
        Input data, must be 1D.

    predicate : function
        A function which operates on sections of the given array, returning
        element-wise True or False for each data value.

    chunk_size : integer
        The length of the chunks to use when searching for matching indices.
        For high probability predicates, a smaller number will make this
        function quicker, similarly choose a larger number for low
        probabilities.

    Returns
    -------
    index_generator : generator
        A generator of (indices, data value) tuples which make the predicate
        True.

    See Also
    --------
    where, nonzero

    Notes
    -----
    This function is best used for finding the first, or first few, data values
    which match the predicate.

    Examples
    --------
    >>> a = np.sin(np.linspace(0, np.pi, 200))
    >>> result = find(a, lambda arr: arr > 0.9)
    >>> next(result)
    ((71, ), 0.900479032457)
    >>> np.where(a > 0.9)[0][0]
    71


    """
    if a.ndim != 1:
        raise ValueError('The array must be 1D, not {}.'.format(a.ndim))

    i0 = 0
    chunk_inds = chain(xrange(chunk_size, a.size, chunk_size),
                 [None])

    for i1 in chunk_inds:
        chunk = a[i0:i1]
        for inds in izip(*predicate(chunk).nonzero()):
            yield (inds[0] + i0, ), chunk[inds]
        i0 = i1

"""
general helpers
===============
"""

def array(gen):
    if hasattr(gen, "__next__"):
        return np.array(list(gen))
    return np.array(gen)


def deepflatten(maybe_iterable):
    return np.array(list(mygenerators.deepflatten(maybe_iterable)))

def complex_reshape(flat, shapes):
    """ reshapes flat into elements with shapes

    Parameters
    ----------
    flat : list
        shall be reshaped
    shapes : list of tuples (shapes)
        will reshape list consecutively into summarizing elements with given shape

    Returns
    -------
    list of reshapes
    """
    for s in shapes:
        length = int(np.prod(s))  # will indeed return 1 for empty shape which denotes scalar
        head, flat = flat[:length], flat[length:]
        yield np.reshape(head, s)


"""
Convenience Wrappers
====================
e.g. in order to work easily with generators in numpy contexts
"""

def mean_gen(values):
    sums = next(values)
    for n, xs in enumerate(values):
        try:
            sums = [x+s for x, s in zip(xs, sums)]
        except:
            sums += xs
    try:
        #needs __future__.division
        return [s/(n+2) for s in sums]
    except:
        return sums/(n+2)

def mean(iterable):
    if hasattr(iterable, "next"):
        return mean_gen(iterable)
    return np.mean(iterable)


