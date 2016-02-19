#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, division
import numpy

__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'

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
    return numpy.mean(iterable)