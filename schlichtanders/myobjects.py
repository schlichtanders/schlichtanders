""" Again a favourit package: Objects for everything. Namespaces, Counts, and something I am really proud of:
``Structure``. A Structure kind of implements a mixture between dicts and nested lists, which is highly useful for
python-like complex access to datastructures. E.g. pyparsing uses a similar interface for its ParseResult. """
from __future__ import print_function, division

from mygenerators import deleteallbutone
from itertools import islice
import cPickle
import sys
from copy import deepcopy
from itertools import count
from collections import Mapping, Sequence, MutableSet
import types
import weakref
from six import string_types


"""
Generally Helpful Objects
=========================
"""
class Namespace(object):
    """ simple class to use as namespace (like a struct object in Matlab) """

    def __init__(self, _dict=None, **kwargs):
        self.__dict__ = kwargs if _dict is None else _dict

Empty = Struct = Namespace


from mycontextmanagers import until_stopped, ignored


class NestedNamespace(object):

    def __init__(self, *instances):
        self.instances = instances

    def __getattr__(self, name):
        for ins in self.instances:
            with ignored(AttributeError):
                return getattr(ins, name)



"""
Structure and Related Objects
=============================
"""


def pickle_deepcopy(o):
    return cPickle.loads(cPickle.dumps(o, -1))

class Count(object):
        """ future-like counting object

        The first time the attribute ``value`` is accessed, it gets computed by counting onwards from the total_count
        """

        # CLASS
        # -----

        total_count = 0
        weakrefs = []

        @staticmethod
        def reset(total_count=0):
            Count.total_count = total_count

        @staticmethod
        def reset_all(total_count=0):
            Count.total_count = total_count
            weakrefs_still_alive = []
            for ref in Count.weakrefs:
                o = ref()
                if o is not None:
                    weakrefs_still_alive.append(ref)
                    o._value = None
            Count.weakrefs = weakrefs_still_alive

        @staticmethod
        def eval_all():
            weakrefs_still_alive = []
            for ref in Count.weakrefs:
                o = ref()
                if o is not None:
                    weakrefs_still_alive.append(ref)
                    o.eval()
            Count.weakrefs = weakrefs_still_alive


        # INSTANCE
        # --------

        def __init__(self, _value=None):
            Count.weakrefs.append(weakref.ref(self))
            self._value = _value


        def __call__(self):
            if self._value is None:
                self._value = Count.total_count
                Count.total_count += 1
            return self._value

        @property
        def value(self):
            if self._value is None:
                self._value = Count.total_count
                Count.total_count += 1
            return self._value

        def eval(self):
            self.value
            return self

        def __str__(self):
            return "?" if self._value is None else str(self._value)

        def __repr__(self):
            return str(self)


# TODO unpickable with pyximport
def create_counter(classname="Count"):
    """ this factory method is used to create independent Count classes
    CAUTION: for pickle to work, the classname must be the same name as the variable this factory-call is set to """

    class Count(object):
        """ future-like counting object

        The first time the attribute ``value`` is accessed, it gets computed by counting onwards from the total_count
        """

        # CLASS
        # -----

        total_count = 0
        weakrefs = []

        @staticmethod
        def reset(total_count=0):
            Count.total_count = total_count

        @staticmethod
        def reset_all(total_count=0):
            Count.total_count = total_count
            weakrefs_still_alive = []
            for ref in Count.weakrefs:
                o = ref()
                if o is not None:
                    weakrefs_still_alive.append(ref)
                    o._value = None
            Count.weakrefs = weakrefs_still_alive

        @staticmethod
        def eval_all():
            weakrefs_still_alive = []
            for ref in Count.weakrefs:
                o = ref()
                if o is not None:
                    weakrefs_still_alive.append(ref)
                    o.eval()
            Count.weakrefs = weakrefs_still_alive


        # INSTANCE
        # --------

        def __init__(self, _value=None):
            Count.weakrefs.append(weakref.ref(self))
            self._value = _value


        def __call__(self):
            if self._value is None:
                self._value = Count.total_count
                Count.total_count += 1
            return self._value

        @property
        def value(self):
            if self._value is None:
                self._value = Count.total_count
                Count.total_count += 1
            return self._value

        def eval(self):
            self.value
            return self

        def __str__(self):
            return "?" if self._value is None else str(self._value)

        def __repr__(self):
            return str(self)


    # For pickling to work, the __module__ variable needs to be set to the frame
    # where the named tuple is created.  Bypass this step in environments where
    # sys._getframe is not defined (Jython for example) or sys._getframe is not
    # defined for arguments greater than 0 (IronPython).
    try:
        Count.__module__ = sys._getframe(1).f_globals.get('__name__', '__main__')
    except (AttributeError, ValueError):
        pass
    Count.__name__ = classname
    return Count





# TODO the whole struct type is jsonable, and thus probably improvable with specific cython

class Structure(Sequence):
    """ implements generic dict-list-combining structure like it is used in pyparsing.ParseResult """


    FLATTEN_LISTS = True
    EMPTY_DEFAULT = "EMPTY"
    LeafError = TypeError, KeyError

    #: By default all key access return lists. With this option set to true, keys delivering singleton [object] will return object directly
    KEY_ACCESS_REDUCE_SINGLETONS = False

    # Construction
    # ------------

    def __init__(self, initializer='None', struct=None, leaves=None):
        """either initializer or non-empty list is needed"""
        if (struct is not None and leaves is None) or (struct is None and leaves is not None):
            raise RuntimeError("if initializing with struct, also leaves have to be given (and reversely)")

        if struct is not None: # then also leaves is not None
            self.struct = struct
            self.leaves = leaves
        elif initializer != 'None':
            self.struct = dict(list=[None], dict={}, pseudo=False, liftedkeys=False, n=1)
            self.leaves = [initializer]
        else:
            self.struct = dict(list=[], dict={}, pseudo=False, liftedkeys=False, n=0)
            self.leaves = []

    def deepcopy(self, memo=None):
        # self struct can be directly passed without copying
        return Structure(struct=self.struct, leaves=pickle_deepcopy(self.leaves))

    # Logic
    # -----

    def clear(self):
        self.struct = dict(list=[], dict={}, pseudo=False, liftedkeys=False, n=0)
        self.leaves = []

    def set_name(self, name):
        iter_self = iter(self)
        next(iter_self)
        try:
            next(iter_self)
            len1 = False
        except StopIteration:
            len1 = True

        if not len1: # make unique first index
            self.group(pseudo=True, liftkeys=True)
        self.struct['dict'][name] = self.struct['dict'].get(name, []) + [0]
        # do everything by index, for faster serialization
        # index refers to self.struct['list']
        return self

    def group(self, wrapper=None, pseudo=False, liftkeys=False):
        """ CAUTION: changes self inplace
        deepcopy before if you like to have a new object

        if wrapper is specified, subgroup is regarded as new Leaf"""
        sub = self.struct
        sub['pseudo'] = pseudo
        sub['liftedkeys'] = liftkeys

        if wrapper is None:
            self.struct = dict(
                    list = [sub],
                    dict = self._lift_keys(sub['dict']) if liftkeys else {},
                    pseudo = False,
                    liftedkeys = False,
                    n = sub['n']
                )
            # keep old leaves
        else:
            self.struct = dict(
                list = [None],
                dict = self._lift_keys(sub['dict']) if liftkeys else {},
                pseudo = False,
                liftedkeys = False,
                n = 1
            )
            self.leaves = [wrapper(Structure(struct=sub, leaves=self.leaves))]

        return self

    @staticmethod
    def _lift_keys(_dict):
        return { k: ['lifted'] for k in _dict.iterkeys() }

    def map(self, func, inplace=True):
        """Structure is a functor =), func is mapped over leaves"""
        # only leaves have to be adapted
        new_leaves = [func(l) for l in self.leaves]
        if inplace:
            self.leaves = new_leaves
            return self
        else:
            return Structure(struct=self.struct, leaves=new_leaves)


    # general interface methods:
    # --------------------------

    def __iter__(self):
        """ flattens out pseudo structures as well as leaves
        final generator interface for user """
        # top level can be assumed to be real structure dict
        # as it is called by `Structure.__iter__`, initialized with `self.__dict__`
        for s in self.iter_withpseudo(): # already flattened out leaves
            if isinstance(s, Structure) and s.struct['pseudo']:
                for t in s: # yield from in python 3.x, calls __iter__
                    yield t
            else:
                yield s #this is already a true leaf, not only a Count

    def iter_withpseudo(self):
        """ flattens out leaves, but not pseudo groups """
        cur_leaf = 0
        for s in self.struct['list']:
            if s is None: #leaf
                leaf = self.leaves[cur_leaf]
                if isinstance(leaf, list) and Structure.FLATTEN_LISTS:
                    for subleaf in leaf:
                        yield subleaf
                else:
                    yield leaf
                cur_leaf += 1
            else:
                yield Structure(struct=s, leaves=self.leaves[cur_leaf : cur_leaf+s['n']])
                cur_leaf += s['n']

    def __getitem__(self, index):
        """ depending on index it gives list entry (for integers) or dictionary entries (for names) """
        try:
            if isinstance(index, int):
                # the only reliable way is to iterate up to the index:
                return next(islice(self, index, None))
            if isinstance(index, slice):
                return list(islice(self, index.start, index.stop, index.step))
            else:
                key_return = list(self._dictitem_gen(index))
                if self.KEY_ACCESS_REDUCE_SINGLETONS and len(key_return) == 1:
                    return key_return[0]
                else:
                    return key_return
        except StopIteration:
            raise IndexError("list index out of range")


    def _dictitem_gen(self, index):
        """ checks for 'lifted' keys and in case flattens out all results """
        # first call can be assumed to work on structure dict
        if index in self.struct['dict']: # "dict" is a standard dictionary, thus iterating over it is the same as iterating over the keys
            for idx in self.struct['dict'][index]: # it is always a list
                if idx == 'lifted':
                    # recursive case
                    for s in self.iter_withpseudo():
                        if isinstance(s, Structure) and s.struct['liftedkeys']:
                            for elem in s._dictitem_gen(index): # yield from in python 3.x:
                                yield elem
                else:
                    # base case
                    elem = self.struct['list'][idx]
                    previous = self.struct['list'][:idx]
                    cur_leaf = sum(1 if s is None else s['n'] for s in previous)

                    if elem is None: # leaf
                        yield self.leaves[cur_leaf]
                    else:
                        yield Structure(struct=elem, leaves=self.leaves[cur_leaf : cur_leaf+elem['n']])

    def __len__(self):
        """ this needs very long to compute """
        return len(list(iter(self)))

    def keys(self):
        return self.struct['dict'].keys()

    def __add__(self, other):
        """ this copies `self` before adding up with `other` """
        base = deepcopy(self)
        base += other # (+=) == __iadd__
        return base

    def __iadd__(self, other):
        if not isinstance(other, Structure):
            raise NotImplementedError("cannot iadd type %s" % type(other))

        otherdict_offset = len(self.struct['list']) # importantly, this is the old list

        for key in other.struct['dict']:
            otherdict_transf = [x + otherdict_offset if x != 'lifted' else x  for x in other.struct['dict'][key]]
            self.struct['dict'][key] = list(deleteallbutone('lifted',
                self.struct['dict'].get(key, []) + otherdict_transf
            ))

        self.struct['list'] += other.struct['list'] # this can be directly used without copying
        self.struct['n'] += other.struct['n']
        # liftedkeys / pseudo are set if the structure is grouped.
        # Top-Level Structures are by default non-pseudo, which makes sense, and also do not have to lift keys
        # self.struct['pseudo'] &= other.struct['pseudo']
        # self.struct['liftedkeys'] |= other.struct['liftedkeys']

        # leaves can just be concatenated
        self.leaves += other.leaves
        return self


    def __str__(self):

        subs = [str(s) for s in self]
        strsubs = ",".join(subs)
        if len(subs) == 1 and self.struct['pseudo']: # if only pseudo groups, ignore them completely, also in str representation
            return strsubs
        else:
            return "[%s]" % strsubs

    @staticmethod
    def _repr_struct(struct, counter=None):
        if counter is None:
            counter = count()
        # [] are for pretty printing, semantically it is rather a ()
        if struct is None:
            return "#%i" % next(counter)
        else:
            return "{'list' : %s, 'dict' : %s, 'pseudo' : %s, 'liftedkeys' : %s}" % (
                "[%s]" % ",".join(Structure._repr_struct(s, counter) for s in struct['list']),
                repr(struct['dict']),
                struct['pseudo'],
                struct['liftedkeys']
            )

    def __repr__(self):
        return "{struct: %s, leaves: %s}" % (self._repr_struct(self.struct), repr(self.leaves))





"""
OrderedSet
==========
"""

def check_deterministic(iterable):
    # Most places where OrderedSet is used, theano interprets any exception
    # whatsoever as a problem that an optimization introduced into the graph.
    # If I raise a TypeError when the DestoryHandler tries to do something
    # non-deterministic, it will just result in optimizations getting ignored.
    # So I must use an assert here. In the long term we should fix the rest of
    # theano to use exceptions correctly, so that this can be a TypeError.
    if iterable is not None:
        if not isinstance(iterable, (
                list, tuple, OrderedSet,
                types.GeneratorType, string_types)):
            if len(iterable) > 1:
                # We need to accept length 1 size to allow unpickle in tests.
                raise AssertionError(
                    "Get an not ordered iterable when one was expected")

# Copyright (C) 2009 Raymond Hettinger
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the
# following conditions:

# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# {{{ http://code.activestate.com/recipes/576696/ (r5)


class Link(object):
    # This make that we need to use a different pickle protocol
    # then the default.  Othewise, there is pickling errors
    __slots__ = 'prev', 'next', 'key', '__weakref__'

    def __getstate__(self):
        # weakref.proxy don't pickle well, so we use weakref.ref
        # manually and don't pickle the weakref.
        # We restore the weakref when we unpickle.
        ret = [self.prev(), self.next()]
        try:
            ret.append(self.key)
        except AttributeError:
            pass
        return ret

    def __setstate__(self, state):
        self.prev = weakref.ref(state[0])
        self.next = weakref.ref(state[1])
        if len(state) == 3:
            self.key = state[2]


class OrderedSet(MutableSet):
    'Set the remembers the order elements were added'
    # Big-O running times for all methods are the same as for regular sets.
    # The internal self.__map dictionary maps keys to links in a doubly linked list.
    # The circular doubly linked list starts and ends with a sentinel element.
    # The sentinel element never gets deleted (this simplifies the algorithm).
    # The prev/next links are weakref proxies (to prevent circular references).
    # Individual links are kept alive by the hard reference in self.__map.
    # Those hard references disappear when a key is deleted from an OrderedSet.

    # Added by IG-- pre-existing theano code expected sets
    #   to have this method
    def update(self, iterable):
        check_deterministic(iterable)
        self |= iterable

    def __init__(self, iterable=None):
        # Checks added by IG
        check_deterministic(iterable)
        self.__root = root = Link()         # sentinel node for doubly linked list
        root.prev = root.next = weakref.ref(root)
        self.__map = {}                     # key --> link
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.__map)

    def __contains__(self, key):
        return key in self.__map

    def add(self, key):
        # Store new key in a new link at the end of the linked list
        if key not in self.__map:
            self.__map[key] = link = Link()
            root = self.__root
            last = root.prev
            link.prev, link.next, link.key = last, weakref.ref(root), key
            last().next = root.prev = weakref.ref(link)

    def union(self, s):
        check_deterministic(s)
        n = self.copy()
        for elem in s:
            if elem not in n:
                n.add(elem)
        return n

    def intersection_update(self, s):
        l = []
        for elem in self:
            if elem not in s:
                l.append(elem)
        for elem in l:
            self.remove(elem)
        return self

    def difference_update(self, s):
        check_deterministic(s)
        for elem in s:
            if elem in self:
                self.remove(elem)
        return self

    def copy(self):
        n = OrderedSet()
        n.update(self)
        return n

    def discard(self, key):
        # Remove an existing item using self.__map to find the link which is
        # then removed by updating the links in the predecessor and successors.
        if key in self.__map:
            link = self.__map.pop(key)
            link.prev().next = link.next
            link.next().prev = link.prev

    def __iter__(self):
        # Traverse the linked list in order.
        root = self.__root
        curr = root.next()
        while curr is not root:
            yield curr.key
            curr = curr.next()

    def __reversed__(self):
        # Traverse the linked list in reverse order.
        root = self.__root
        curr = root.prev()
        while curr is not root:
            yield curr.key
            curr = curr.prev()

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        if last:
            key = next(reversed(self))
        else:
            key = next(iter(self))
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        # Note that we implement only the comparison to another
        # `OrderedSet`, and not to a regular `set`, because otherwise we
        # could have a non-symmetric equality relation like:
        #       my_ordered_set == my_set and my_set != my_ordered_set
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        elif isinstance(other, set):
            # Raise exception to avoid confusion.
            raise TypeError(
                'Cannot compare an `OrderedSet` to a `set` because '
                'this comparison cannot be made symmetric: please '
                'manually cast your `OrderedSet` into `set` before '
                'performing this comparison.')
        else:
            return NotImplemented

# end of http://code.activestate.com/recipes/576696/ }}}
