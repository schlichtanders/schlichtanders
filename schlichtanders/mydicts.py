#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division

__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'


def update(dict1, dict2, overwrite=True, append=True):
    """ overwrites dict1 with dict2

    :param dict1:
    :param dict2:
    :param overwrite:
    :param append:
    :return:
    """
    if overwrite and append:
        dict1.update(dict2)
    if overwrite and not append:
        for k in dict1:
            if k in dict2:
                dict1[k] = dict2[k]
    if not overwrite and append:
        for k in dict2:
            if k not in dict1:
                dict1[k] = dict2[k]



# fancy remappings =)

from .myfunctools import use_as_needed
from itertools import chain
from collections import Mapping


class ComposeDicts(Mapping):

    COMPOSE_TYPES = ["stack", "call", 'use_as_needed']

    def __init__(self, dict1, dict2, compose_type="stack", if_dict1_empty_iterate_over_dict2=False):
        self.dict1 = dict1
        self.dict2 = dict2
        self.compose_type = compose_type
        self.if_dict1_empty_iterate_over_dict2 = if_dict1_empty_iterate_over_dict2

    def __getitem__(self, item):
        try:
            return getattr(self, "_getitem_%s" % self.compose_type)(item)
        except AttributeError:
            raise ValueError("`compose_type` %s is not supported. Should be e.g. one in [%s]."
                             % (self.compose_type, ",".join(ComposeDicts.COMPOSE_TYPES)))

    def _getitem_stack(self, item):
        return self.dict2[self.dict1[item]]

    def _getitem_call(self, item):
        return self.dict1[item](self.dict2)

    def _getitem_use_as_needed(self, item):
        return use_as_needed(self.dict1, self.dict2)

    def __len__(self):
        l = len(self.dict1)
        if l == 0 and self.if_dict1_empty_iterate_over_dict2:
            return len(self.dict2)
        else:
            return l

    def __iter__(self):
        if len(self.dict1) == 0 and self.if_dict1_empty_iterate_over_dict2:
            return iter(self.dict2)
        else:
            return iter(self.dict1)


class identity_dict(dict):
    def __getitem__(self, item):
        try:
            return super(identity_dict, self).__getitem__(item)
        except KeyError:
            return item

