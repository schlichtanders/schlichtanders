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


class ComposedDictsView(Mapping):
    """ composes two dictionaries with the given compose method """

    COMPOSE_TYPES = ["stack", "call", 'use_as_needed', 'defaultto', 'overwrite']

    def __init__(self, dict1, dict2, compose_type="stack", if_dict1_empty_iterate_over_dict2=False):
        """
        constructs a view on a composition of dict1 and dict2
        :param dict1: keys become keys of the view
        :param dict2: gets composed
        :param compose_type:
            Specifies method, how the values of the two dicts get composed. Defaults to 'stack'.
            =============== ======================================================
            compose_type    meaning
            =============== ======================================================
            'stack'         self[key] = dict2[dict1[key]]
            'call'          self[key] = dict1[key](dict2)
            'use_as_needed  self[key] = use_as_needed(dict1[key], dict2)
            'defaultto'     self[key] = dict1[key] if key in dict1 else dict2[key]
            'overwrite'     self[key] = dict2[key] if key in dict2 else dict1[key]
            =============== ======================================================

        :param if_dict1_empty_iterate_over_dict2:
            if True and dict1 is empty then the view's __iter__ method calls iter(dict2) instead
        """
        self.dict1 = dict1
        self.dict2 = dict2
        self.compose_type = compose_type
        self.if_dict1_empty_iterate_over_dict2 = if_dict1_empty_iterate_over_dict2

    def __getitem__(self, item):
        try:
            return getattr(self, "_getitem_%s" % self.compose_type)(item)
        except AttributeError:
            raise ValueError("`compose_type` %s is not supported. Should be e.g. one in [%s]."
                             % (self.compose_type, ",".join(ComposedDictsView.COMPOSE_TYPES)))

    def _getitem_stack(self, item):
        return self.dict2[self.dict1[item]]

    def _getitem_call(self, item):
        return self.dict1[item](self.dict2)

    def _getitem_use_as_needed(self, item):
        return use_as_needed(self.dict1, self.dict2)

    def _getitem_defaultto(self, item):
        return self.dict1[item] if item in self.dict1 else self.dict2[item]

    def _getitem_overwrite(self, item):
        return self.dict2[item] if item in self.dict2 else self.dict1[item]

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


class DefaultDict(dict):
    """
    like ``collections.defaultdict``, however default method is called with the accessed key
    """
    def __init__(self, default_getitem=lambda key: key, **kwargs):
        """ constructs a DefaultDict

        :param default_getitem: defaults to returning the same key, i.e. like an identity function
        :param kwargs: kwargs for standard dict initializations
        """
        self.default_getitem = default_getitem
        super(DefaultDict, self).__init__(**kwargs)

    def __getitem__(self, key):
        try:
            return super(DefaultDict, self).__getitem__(key)
        except KeyError:
            return self.default_getitem(key)

