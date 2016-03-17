#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, division

__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'

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