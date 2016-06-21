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
    return dict1



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


class ModifyDict(Mapping):
    def __init__(self, base_dict, modify_getitem=lambda key, value: value):
        self.base_dict = base_dict
        self.modify_getitem = modify_getitem

    def __getitem__(self, item):
        return self.modify_getitem(item, self.base_dict[item])

    def __iter__(self):
        return iter(self.base_dict)

    def __len__(self):
        return len(self.base_dict)


class DefaultDict(dict):
    """
    like ``collections.defaultdict``, however default method is called with the accessed key
    """
    def __init__(self, default_getitem=None, default_setitem=None, default_delitem=None, *args, **kwargs):
        """ constructs a DefaultDict

        :param default_getitem: defaults to returning the same key, i.e. like an identity function
        :param kwargs: kwargs for standard dict initializations
        """
        # if either parameter is not callable, regard it as additional arg
        if default_delitem is not None and not hasattr(default_delitem, '__call__'):
            args = (default_delitem,) + args
            default_delitem = None
        if default_setitem is not None and not hasattr(default_getitem, '__call__'):
            args = (default_setitem,) + args
            default_setitem = None
        if default_getitem is not None and not hasattr(default_getitem, '__call__'):
            args = (default_getitem,) + args
            default_getitem = None

        self.default_getitem = super(DefaultDict, self).__getitem__ if default_getitem is None else default_getitem
        self.default_setitem = super(DefaultDict, self).__setitem__ if default_setitem is None else default_setitem
        self.default_delitem = super(DefaultDict, self).__delitem__ if default_delitem is None else default_delitem

        self.expand = True
        super(DefaultDict, self).__init__(*args, **kwargs)

    def noexpand(self):
        self.expand = False
        return self

    def __getitem__(self, key):
        try:
            return super(DefaultDict, self).__getitem__(key)
        except KeyError:
            value = self.default_getitem(key)
            if self.expand:
                super(DefaultDict, self).__setitem__(key, value)  # super needed as setitem may be overwritten too
            return value

    def __setitem__(self, key, value):
        if key in self:
            super(DefaultDict, self).__setitem__(key, value)
        else:
            self.default_setitem(key, value)

    def __delitem__(self, key):
        if key in self:
            super(DefaultDict, self).__delitem__(key)
        else:
            self.default_delitem(key)


class IdentityDict(DefaultDict):
    """ almost like defaultdict, with the crucial difference that new keys are not added dynamically, but always regenerated """
    def __init__(self, *args, **kwargs):
        """ see DefaultDict for signature """
        super(IdentityDict, self).__init__(*args, **kwargs)
        self.expand = False

    def set_expand(self):
        self.expand = True


class PassThroughDict(IdentityDict):
    """ postmap which passes everything through model if not further defined """
    def __init__(self, dict_like, *args, **kwargs):
        super(PassThroughDict, self).__init__(
            dict_like.__getitem__,
            dict_like.__setitem__,
            dict_like.__delitem__,
            *args,
            **kwargs
        )


class FrozenDict(Mapping):
    # taken from http://stackoverflow.com/questions/2703599/what-would-a-frozen-dict-be
    """ This is a hashable wrapper around a dict interface """

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        self._hash = None

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __getitem__(self, key):
        return self._d[key]

    def __hash__(self):
        # It would have been simpler and maybe more obvious to
        # use hash(tuple(sorted(self._d.iteritems()))) from this discussion
        # so far, but this solution is O(n). I don't know what kind of
        # n we are going to run into, but sometimes it's hard to resist the
        # urge to optimize when it will gain improved algorithmic performance.
        if self._hash is None:
            self._hash = 0
            for pair in self.iteritems():
                self._hash ^= hash(pair)
        return self._hash