from __future__ import division
import collections
import numpy


class defaultdict(collections.defaultdict):
    """ just overwrites representation methods of defaultdict type, nothing more """
    def __str__(self):
        return str(dict(self.items()))
    def __repr__(self):
        return str(self)

def str_list(l):
    return '[' + ','.join(map(str, l)) + ']'


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
