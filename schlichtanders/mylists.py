#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Like mygenerators, there specific often needed utilities for lists. I really like the ``as_list`` decorator for
an empty args generator. Also, take a look at DictList.
"""
from __future__ import print_function, division
from collections import MutableSequence, Mapping, Sequence
from copy import deepcopy, copy
import operator as op
import mygenerators
import wrapt

__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'

@wrapt.decorator
def return_list(wrapped, instance, args, kwargs):
    return list(wrapped(*args, **kwargs))

def as_list(gen):
    """ generator decorator which executes the generator and returns results as list"""
    return list(gen())


def sequencefy(o):
    return o if isinstance(o, Sequence) else [o]


def findall(l, o):
    """ find all indices from list ``l`` where entries match specific object ``o``

    :param l: list to search in
    :param o: object to search for
    :return: list of indices where l[i] == o
    """
    return [i for i, u in enumerate(l) if u==o]

def getall(l, idx):
    """ get all entries of list ``l`` at positions ``idx``

    :param l: list
    :param idx: indices
    :return: respective sublist
    """
    return [l[i] for i in idx]


def remove_duplicates(l):
    """ removes duplicates in place by using del call """
    unique = set()  # we use a set because ``elem in set`` is much faster than ``elem in list``
    i = 0
    while i < len(l):
        elem = l[i]
        if elem in unique:
            del l[i]
        else:
            unique.add(elem)
            i += 1
    return l


def add_up(iterable):
    return reduce(op.add, iterable)


def deepflatten(maybe_iterable):
    return list(mygenerators.deepflatten(maybe_iterable))


def shallowflatten(maybe_iterable):
    return list(mygenerators.shallowflatten(maybe_iterable))


class DictList(MutableSequence):
    """
    firstly, this is a list
    secondly, this is a dict pointing to lists of elements in DictList (kept unique, i.e. automatically removing duplicates)
    """
    def __init__(self, *list_entries, **names_to_list_of_list_entries):
        self.list = list_entries
        self.dict = names_to_list_of_list_entries
        # update all dictionary keys, keeping only references pointing to the list
        for k in self.dict:
            self.dict[k] = [v for v in self.dict[k] if v in self.list]

    def __copy__(self):
        return DictList(*self.list, **self.dict)

    # merged list-dict interface
    # --------------------------

    def __getitem__(self, item):
        if isinstance(item, basestring):
            return self.dict[item]
        else:
            return self.list[item]

    def __setitem__(self, key, new):
        """ key types supported: string, int

        maintains references to values in the list """

        if isinstance(key, basestring):
            self.dict[key] = [v for v in new if v in self.list]
        elif isinstance(key, int):
            old = self.list[key]
            self.list[key] = new
            # update all dictionary keys:
            for k in self.dict:
                self.dict[k] = [new if v is old else v for v in self.dict[k]]
        else:
            raise NotImplementedError("only string and int are allowed as keys for setting (e.g. no slices!)")

    def __delitem__(self, key):
        """ key types supported: string, int, slice """
        if isinstance(key, basestring):
            # this makes most sense if value refers to elements in the list
            del self.dict[key]
        else:
            del self.list[key]
            # update all dictionary keys:
            for k in self.dict:
                self.dict[k] = [v for v in self.dict[k] if v in self.list]
            # could be made more efficient by looking at the concrete key-index, but this way it is much simpler to read =)

    # list-like interface
    # -------------------

    def __iter__(self):
        return iter(self.list)

    def __len__(self):
        return len(self.list)

    # Operators
    # ---------

    def __add__(self, other):
        cp = copy(self)
        cp += other
        return cp

    def __iadd__(self, other):
        if isinstance(other, MutableSequence):
            self.list += other
        elif isinstance(other, DictList):
            self.list += other.list
            for k in other.dict:
                if k in self.dict:
                    self.dict[k] += other.dict[k]
                    remove_duplicates(self.dict[k])
                else:
                    self.dict[k] = other.dict[k]
        else:
            raise NotImplemented
        return self

    def __radd__(self, other):
        if isinstance(other, MutableSequence):
            return DictList(*(other + self.list), **self.dict)
        raise NotImplemented


    # Proxy Mapping interface of self.dict (methods copied from collections.Mapping)
    # ------------------------------------

    def get(self, key, default=None):
        'D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None.'
        return self.dict.get(key, default)

    def iterkeys(self):
        'D.iterkeys() -> an iterator over the keys of D'
        return self.dict.iterkeys()

    def itervalues(self):
        'D.itervalues() -> an iterator over the values of D'
        return self.dict.itervalues()

    def iteritems(self):
        'D.iteritems() -> an iterator over the (key, value) items of D'
        return self.dict.iteritems()

    def keys(self):
        "D.keys() -> list of D's keys"
        return self.dict.keys()

    def items(self):
        "D.items() -> list of D's (key, value) pairs, as 2-tuples"
        return self.dict.items()

    def values(self):
        "D.values() -> list of D's values"
        return self.dict.values()

    def insert(self, index, value):
        self.list.insert(index, value)
