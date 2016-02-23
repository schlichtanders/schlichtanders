from mygenerators import deleteallbutone
from itertools import islice
import cPickle
import ujson
import weakref

from copy import deepcopy
def pickle_deepcopy(o):
    return cPickle.loads(cPickle.dumps(o, -1))


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
            self.struct = dict(list=[0], dict={}, pseudo=False, liftedkeys=False)
            self.leaves = [initializer]
        else:
            self.struct = dict(list=[], dict={}, pseudo=False, liftedkeys=False)
            self.leaves = []

    def deepcopy(self, memo=None):
        # self struct can be directly passed without copying
        return Structure(struct=self.struct, leaves=pickle_deepcopy(self.leaves))

    # Logic
    # -----

    def clear(self):
        self.struct = dict(list=[], dict={}, pseudo=False, liftedkeys=False)
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
                    liftedkeys = False
                )
            # keep old leaves
        else:
            self.struct = dict(
                list = [0],
                dict = self._lift_keys(sub['dict']) if liftkeys else {},
                pseudo = False,
                liftedkeys = False
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
                yield s

    def iter_withpseudo(self):
        """ flattens out leaves, but not pseudo groups """
        for s in self.struct['list']:
            if isinstance(s, int): #leaf
                leaf = self.leaves[s]
                if isinstance(leaf, list) and Structure.FLATTEN_LISTS:
                    for subleaf in leaf:
                        yield subleaf
                else:
                    yield leaf
            else:
                yield Structure(struct=s, leaves=self.leaves)

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

                    if isinstance(elem, int):
                        yield self.leaves[elem]
                    else:
                        yield Structure(struct=elem, leaves=self.leaves) #TODO as before, these leaves work, however are inefficient for map, as much stays unused

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

    @staticmethod
    def _get_offset(struct):
        """ traverses struct reversely until it finds leaf """
        for r in reversed(struct['list']):
            if isinstance(r, int):
                return r + 1 # offset is one bigger than biggest int, as we start counting with 0
            else:
                sub_offset = Structure._get_offset(r)
                if sub_offset is not None:  # means that return was called, i.e. offset found
                    return sub_offset

    @staticmethod
    def _add_offset(offset, struct_list):
        for i, s in enumerate(struct_list):
            if isinstance(s, int):
                struct_list[i] = s + offset
            else:
                Structure._add_offset(offset, s['list'])
        return struct_list

    def __iadd__(self, other):
        if not isinstance(other, Structure):
            raise NotImplementedError("cannot iadd type %s" % type(other))

        otherdict_offset = len(self.struct['list']) # importantly, this is the old list

        for key in other.struct['dict']:
            otherdict_transf = [x + otherdict_offset if x != 'lifted' else x  for x in other.struct['dict'][key]]
            self.struct['dict'][key] = list(deleteallbutone('lifted',
                self.struct['dict'].get(key, []) + otherdict_transf
            ))

        otherlist_offset = Structure._get_offset(self.struct)

        # copy struct for _add_offset
        # TODO this is not necessary when using Counts instead of int, as no _add_offset is needed either,
        # however then ujson is also no longer possible, but probably the struct then has not to be copied at all
        # up to now, I think this is only used for construction, as repetitions just store lists
        # Downside of Counts: every iteration needs a bit longer (i.e. for checking whether Count is set already),
        # but iterations are also only needed for user side, not for parsing

        other_list = ujson.loads(ujson.dumps(other.struct['list']))
        if otherlist_offset is not None:
            Structure._add_offset(otherlist_offset, other_list)
        self.struct['list'] += other_list
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
        if isinstance(struct, int):
            return repr(struct)
        else:
            return "{'list' : %s, 'dict' : %s, 'pseudo' : %s, 'liftedkeys' : %s}" % (
                "[%s]" % ",".join(Structure._repr_struct(s) for s in struct['list']),
                repr(struct['dict']),
                struct['pseudo'],
                struct['liftedkeys']
            )

    def __repr__(self):
        return "{struct: %s, leaves: %s}" % (self._repr_struct(self.struct), repr(self.leaves))