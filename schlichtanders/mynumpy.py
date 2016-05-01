#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, division
import numpy
import numpy as np
import mygenerators
__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'

"""
general helpers
===============
"""

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


