from __future__ import division
import collections


class defaultdict(collections.defaultdict):
    """ just overwrites representation methods of defaultdict type, nothing more """
    def __str__(self):
        return str(dict(self.items()))
    def __repr__(self):
        return str(self)

def str_list(l):
    return '[' + ','.join(map(str, l)) + ']'
