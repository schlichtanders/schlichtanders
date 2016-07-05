""" Convenience method to generate specific arrays/matrices."""


import pylab as pl
import itertools as it
from itertools import izip
import operator as op


def indices(array_like):
    shape = pl.shape(array_like)
    mesh = pl.meshgrid(*(pl.arange(n) for n in shape), indexing='ij') #ij indexing is like it.product
    return izip(*(dim.flat for dim in mesh))


def mrow(*args, **kwargs):
    if isinstance(args[0], pl.ndarray):
        return args[0].ravel().view(pl.matrix)
    return pl.matrix(pl.arange(*args, **kwargs))

def mcol(*args, **kwargs):
    if isinstance(args[0], pl.ndarray):
        return args[0].ravel().view(pl.matrix).T
    return pl.matrix(pl.arange(*args, **kwargs)).T

def row(*args, **kwargs):
    if isinstance(args[0], pl.ndarray):
        return args[0].view(pl.ndarray).ravel()[None]
    return pl.arange(*args, **kwargs)[None]

def col(*args, **kwargs):
    if isinstance(args[0], pl.ndarray):
        return args[0].view(pl.ndarray).ravel()[:,None]
    return pl.arange(*args, **kwargs)[:,None]

def drow(*args, **kwargs):
    if isinstance(args[0], pl.ndarray):
        return args[0].view(pl.ndarray).ravel()[None, :, None]
    return pl.arange(*args, **kwargs)[None, :, None]

def dcol(*args, **kwargs):
    if isinstance(args[0], pl.ndarray):
        return args[0].view(pl.ndarray).ravel()[:,None, None]
    return pl.arange(*args, **kwargs)[:,None, None]

def depth(*args, **kwargs):
    if isinstance(args[0], pl.ndarray):
        return args[0].view(pl.ndarray).ravel()[None, None]
    return pl.arange(*args, **kwargs)[None, None]

def A(a):
    return a.view(pl.ndarray)

def M(a):
    return a.view(pl.matrix)
