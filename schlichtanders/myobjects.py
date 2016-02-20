from collections import Sequence
from mywrappers import defaultdict
from mygenerators import deleteallbutone
from copy import copy
from itertools import islice
import cPickle

def deepcopy(o):
    return cPickle.loads(cPickle.dumps(o, -1))

class Count(object):
    """ future-like counting object
    
    The first time the attribute ``value`` is accessed, it gets computed by counting onwards from the total_count
    """
    total_count = 0
    
    @staticmethod
    def reset(total_count=0):
        Count.total_count = total_count
        
    def __init__(self, _value=None):
        self._value = _value
    
    def __copy__(self):
        return Count(self._value)
    
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


class Leaf(object):
    """ this class just denotes a Leaf of a (nested) Structure
    
    these are the base elements for the functor (map) ability
    
    further Leafs with pseudorgroup structure as element will be flatten out
    in the final Structure and thus they are not visible at all
    """
    FLATTEN_LISTS = True
    EMPTY_DEFAULT = None
    
    def __init__(self, leaf):
        self.leaf = leaf
        
    def map(self, func):
        self.leaf = func(self.leaf)
    
    def __str__(self):
        return str(self.leaf)
    
    def __repr__(self):
        return repr(self.leaf)
    
    def __iter__(self):
        if Leaf.FLATTEN_LISTS and isinstance(self.leaf, list):
            if not self.leaf:
                yield Leaf.EMPTY_DEFAULT
            else:
                for s in self.leaf:
                    yield s
        else:
            yield self.leaf


class Structure(Sequence):
    """ implements generic dict-list-combining structure like it is used in pyparsing.ParseResult """
    
    # Construction
    # ------------
    
    def __init__(self, initializer=None, _list=None, _dict=None):
        """either initializer or non-empty list is needed"""
        if _list is None and initializer is None:
            raise RuntimeError("either _list or initializer is needed")
        self._list = _list if _list is not None else [Leaf(initializer)] # list of sub-Structures
        self._dict = _dict if _dict is not None else defaultdict(list)
        self.pseudo = False # for better recursive iteration, this indicates that the top-level should be flattened by default
        self.liftedkeys = False

    # Logic
    # -----

    def clear(self):
        self._list = []
        self._dict = defaultdict(list)
        self.pseudo = False
        self.liftedkeys = False
    
    def set_name(self, name):
        self.group(pseudo=True, liftkeys=True)
        #self._list[0] is old self before grouping, mind this is equal to self[0], however latter access is much slower
        self._extend_dict({name: [self._list[0]]})
        return self

    def group(self, wrapper=lambda x:x, pseudo=False, liftkeys=False):
        """ CAUTION: changes self inplace
        deepcopy before if you like to have a new object """
        self.pseudo = pseudo
        self.liftedkeys = liftkeys
        
        cp = copy(self)
        Structure.__init__(self,
            _list = [wrapper(cp)],
            _dict = self._lift_keys(cp._dict) if liftkeys else defaultdict(list)
        )
        return self       
    
    @staticmethod 
    def _lift_keys(_dict):
        return defaultdict(
            list,
            { k: ['lifted'] for k in _dict.iterkeys() }
        )
                    
    def map(self, func):
        """Structure is a functor =), func is mapped over leaves
        
        CAUTION:everything is inplace,
        deepcopy before if you want to have a new object"""
        # this works as leaves .map function, thereby references are preserved
        # (otherwise we would have to handle indexes and could not use generators that easily)
        for leaf in self.iter_leaves():
            leaf.map(func)
        return self
    
    
    # general interface methods:
    # --------------------------
    def __iter__(self):
        """ flattens out pseudo structures as well as leaves
        final generator interface for user """
        for s in self.iter_nopseudo():
            # isinstance check is needed as also final leaf-values get yielded
            if isinstance(s, Structure) and s.pseudo:
                for s2 in s: # yield from in python 3.x, calls __iter__
                    yield s2
            else:
                yield s

    def iter_nopseudo(self):
        """ go through structure, regarding pseudogroups as normal groups,
        but flattening leaves (and possible sub-structures there) """
        for s in self._list:
            # flatten out Leaves:
            if isinstance(s, Leaf):
                for s2 in s: # yield from
                    yield s2
            else:
                yield s
        
    def iter_leaves(self):
        """ go through all leaves, mainly used for map """
        # TODO next biggest speed bottleneck, but still a factor of 20 after cPickling
        # maybe check whether one can cythonize this method, but code already seems rather easy
        # as of today, cython is not able to handle `yield`
        for s in self._list:
            if isinstance(s, Leaf):
                yield s
            else:
                for s2 in s.iter_leaves(): #yield from
                    yield s2
                    
    def __getitem__(self, index):
        """ depending on index it gives list entry (for integeres) or dictionary entries (for names) """
        if isinstance(index, int):
            return next(islice(self, index, None))  #TODO relatively inefficient I think! (but won't be really needed neither)
        if isinstance(index, slice):
            return list(islice(self, index.start, index.stop, index.step))
        else:
            return list(self._dictitem_gen(index))
    
    def _dictitem_gen(self, index):
        """ checks for 'lifted' keys and in case flattens out all results """
        if index in self.keys():
            ret = self._dict[index]
            for elem in ret:
                if elem == 'lifted':
                    # this key "lifted" ensures that sublevel is still build from structures
                    # at least I hope so =), so no direct values, but Structure
                    # Nope it does not, because of pseudo structures
                    for s in self.iter_nopseudo():
                        if hasattr(s, "liftedkeys") and s.liftedkeys:
                            # yield from in python 3.x:
                            for i in s._dictitem_gen(index):
                                yield i
                else:
                    yield elem        
                    
    def __len__(self):
        """ this needs very long to compute """
        return len(list(iter(self)))
                    
    def keys(self):
        return self._dict.keys()
        
    def __add__(self, other):
        """ this copies `self` before adding up with `other` """
        base = deepcopy(self)
        base += other # (+=) == __iadd__
        return base
    
    def __call__(self, name):
        return copy(self).set_name(name)
        
    def __iadd__(self, other):
        if not isinstance(other, Structure):
            raise NotImplemented
        self._list += other._list
        self._extend_dict(other._dict)
        return self
    
    def _extend_dict(self, other_dict):
        """ extends self._dict by other_dict however keeps only one 'lifted' entry"""
        for key in other_dict:
            self._dict[key] = list(deleteallbutone('lifted',
                self._dict[key] + other_dict[key]
            ))
            
    def __str__(self):
        strs = [str(i) for i in self]
        return "[" + ",".join(strs)+ "]"
    
    def __repr__(self):
        public_attr = {attr:getattr(self, attr)
                       for attr in dir(self)
                       if not attr.startswith("_") and attr not in dir(self.__class__)}
        if public_attr:
            return "(%s, %s, %s)"%(repr(self._list), repr(self._dict), repr(public_attr))
        else:
            return "(%s, %s,)"%(repr(self._list), repr(self._dict))
