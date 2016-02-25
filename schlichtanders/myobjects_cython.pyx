from gst._gst import Structure

from mygenerators import deleteallbutone
from itertools import islice
import cPickle
import weakref
import sys

from copy import deepcopy
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

class Structure(object):
    """ implements generic dict-list-combining structure like it is used in pyparsing.ParseResult """


    FLATTEN_LISTS = True
    EMPTY_DEFAULT = "EMPTY"
    LeafError = TypeError, KeyError

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
        if isinstance(index, int):
            return next(islice(self, index, None))  #TODO relatively inefficient I think! (but won't be really needed neither)
        if isinstance(index, slice):
            return list(islice(self, index.start, index.stop, index.step))
        else:
            return list(self._dictitem_gen(index))


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
    def _repr_struct(struct):
        # [] are for pretty printing, semantically it is rather a ()
        if struct is None:
            return repr(None)
        else:
            return "{'list' : %s, 'dict' : %s, 'pseudo' : %s, 'liftedkeys' : %s}" % (
                "[%s]" % ",".join(Structure._repr_struct(s) for s in struct['list']),
                repr(struct['dict']),
                struct['pseudo'],
                struct['liftedkeys']
            )

    def __repr__(self):
        return "{struct: %s, leaves: %s}" % (self._repr_struct(self.struct), repr(self.leaves))