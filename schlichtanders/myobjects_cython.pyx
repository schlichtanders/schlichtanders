from mygenerators import deleteallbutone
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




class Structure(object):
    """ implements generic dict-list-combining structure like it is used in pyparsing.ParseResult """


    FLATTEN_LISTS = True
    EMPTY_DEFAULT = "EMPTY"
    LeafError = TypeError, KeyError

    # Construction
    # ------------

    def __init__(self, initializer=None, _list=None, _dict=None):
        """either initializer or non-empty list is needed"""
        # _list is still there for interface compatibility with the standard Structure implementation
        self._substructs_list = (
            _list          if _list is not None else
            [initializer]  if initializer is not None else
            []
        ) # later list of sub-Structures
        self._dict = _dict if _dict is not None else {}
        self.pseudo = False # for better recursive iteration, this indicates that the top-level should be flattened by default
        self.liftedkeys = False

    @staticmethod
    def classify(struct):
        """ wrappes struct into FastStructure class
        :param struct: __dict__ of FastStructure
        :return: FastStructure instance
        """
        s = Structure.__new__(Structure)
        s.__dict__ = struct
        return s

    # Logic
    # -----

    def clear(self):
        self._substructs_list= []
        self._dict = {}
        self.pseudo = False
        self.liftedkeys = False

    def set_name(self, name):
        self.group(pseudo=True, liftkeys=True)
        self._dict[name] = self._dict.get(name, []) + [0] # do everything by index, for faster serialization
        return self

    def group(self, wrapper=lambda x:x, pseudo=False, liftkeys=False):
        """ CAUTION: changes self inplace
        deepcopy before if you like to have a new object """
        self.pseudo = pseudo
        self.liftedkeys = liftkeys

        sub = self.__dict__
        self.__dict__ = {} # set new dict
        Structure.__init__(self,
                           _list = [wrapper(sub)],
                           _dict = self._lift_keys(sub['_dict']) if liftkeys else {}
                           )
        return self

    @staticmethod
    def _lift_keys(_dict):
        return { k: ['lifted'] for k in _dict.iterkeys() }

    def map(self, func):
        """Structure is a functor =), func is mapped over leaves

        CAUTION:everything is inplace,
        deepcopy before if you want to have a new object"""
        self._map(self.__dict__, func)
        return self

    @staticmethod
    def _map(struct, func):
        """ works in place
        :param struct: FastStructure.__dict__
        :param func: to be mapped over leafs
        :return: references to struct
        """
        # TODO biggest bottleneck, and further this does not use yields.. thus could be improved with cython
        # the very top level is supposed to be called by FastStructure.map, i.e. be a true structure dict
        for i, s in enumerate(struct['_substructs_list']):
            try:
                Structure._map(s, func)
            except Structure.LeafError:
                # this happens exactly then, if s is not a structure
                # assuming that the leafs don't have a '_substructs_list'
                # (the rather long name was chosen for this very reason)
                struct['_substructs_list'][i] = func(struct['_substructs_list'][i])
        return struct # just for convenience


    # general interface methods:
    # --------------------------

    def __iter__(self):
        for s in self.iter_flatpseudo(self.__dict__):
            try:
                s['_substructs_list'] # TODO this seems so far the easiest and securest check whether we a substructure
                yield Structure.classify(s)
            except Structure.LeafError: # leaf
                yield s

    @staticmethod
    def iter_flatpseudo(struct):
        """ flattens out pseudo structures as well as leaves
        final generator interface for user """
        # top level can be assumed to be real structure dict
        # as it is called by `FastStructure.__iter__`, initialized with `self.__dict__`
        for s in Structure.iter_withpseudo(struct): # already flattened out leaves
            try:
                if s['pseudo']:
                    for t in Structure.iter_flatpseudo(s): # yield from in python 3.x, calls __iter__
                        yield t
                else:
                    # even if this is not a substructure,
                    # there is no harm, as we do the same if the key is not available
                    yield s
            except Structure.LeafError:
                # gets thrown both if 'pseudo' or '_substructs_list' is not available
                # (the latter is asked for within `FastStructure.iter_withpseudo`),
                # i.e. we have a leaf content which was not flattend out by default (i.e. e.g. no list)
                yield s

    @staticmethod
    def iter_withpseudo(struct):
        """ go through structure, regarding pseudogroups as normal groups,
        but flattening leaves """
        for s in struct['_substructs_list']:
            if Structure.FLATTEN_LISTS and isinstance(s, list): # this would be a leaf, as structures are represented by dicts
                if not s: # empty list is default EMPTY value
                    yield Structure.EMPTY_DEFAULT
                else:
                    for t in s:
                        yield t
            else:
                yield s

    def iter_leaves(self):
        """ go through all leaves, mainly used for map """
        raise NotImplementedError("map works directly, without using iter_leaves. Use map instead")

    def __getitem__(self, index):
        """ depending on index it gives list entry (for integers) or dictionary entries (for names) """
        if isinstance(index, int):
            return next(islice(self, index, None))  #TODO relatively inefficient I think! (but won't be really needed neither)
        if isinstance(index, slice):
            return list(islice(self, index.start, index.stop, index.step))
        else:
            return list(self._dictitem_gen(self.__dict__, index))

    @staticmethod
    def _dictitem_gen(struct, index):
        """ checks for 'lifted' keys and in case flattens out all results """
        # first call can be assumed to work on structure dict
        if index in struct['_dict']: # "_dict" is a standard dictionary, thus iterating over it is the same as iterating over the keys
            for idx in struct['_dict'][index]: # it is always a list
                if idx == 'lifted':
                    # recursive case
                    for s in Structure.iter_withpseudo(struct):
                        try:
                            if s['liftedkeys']:
                                for elem in Structure._dictitem_gen(s, index): # yield from in python 3.x:
                                    yield elem
                        except (TypeError, KeyError):
                            pass
                else:
                    # base case
                    elem = struct['_substructs_list'][idx]
                    try:
                        elem['_substructs_list'] # TODO this seems so far the easiest and securest check whether we have a substructure
                        yield Structure.classify(elem)
                    except Structure.LeafError: # leaf
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

    def __iadd__(self, other):
        if not isinstance(other, Structure):
            raise NotImplementedError("cannot iadd type %s" % type(other))

        otherdict_offset = len(self._substructs_list) # importantly, this is the old _substructs_list

        for key in other._dict:
            otherdict_transf = [x + otherdict_offset if x != 'lifted' else x  for x in other._dict[key]]
            self._dict[key] = list(deleteallbutone('lifted',
                self._dict.get(key, []) + otherdict_transf
            ))

        self._substructs_list += other._substructs_list
        # liftedkeys / pseudo are set if the structure is grouped.
        # Top-Level Structures are by default non-pseudo, which makes sense, and also do not have to lift keys
        # self.pseudo &= other.pseudo
        # self.liftedkeys |= other.liftedkeys
        return self


    @staticmethod
    def _str_struct(struct):
        try:
            subs = [Structure._str_struct(s) for s in Structure.iter_flatpseudo(struct)]
            strsubs = ",".join(subs)
            if len(subs) == 1 and struct['pseudo']:
                return strsubs
            else:
                return "[%s]" % strsubs
        except Structure.LeafError:
            # this hopefuly is a leaf content
            return str(struct)

    @staticmethod
    def _repr_struct(struct):
        # [] are for pretty printing, semantically it is rather a ()
        try:
            return "{'_list' : %s, '_dict' : %s, 'pseudo' : %s, 'liftedkeys' : %s}" % (
                "[%s]" % ",".join(Structure._repr_struct(s) for s in Structure.iter_withpseudo(struct)),
                repr(struct['_dict']),
                struct['pseudo'],
                struct['liftedkeys']
            )
        except Structure.LeafError:
            # this hopefuly is a leaf content
            return repr(struct)

    def __str__(self):
        return self._str_struct(self.__dict__)

    def __repr__(self):
        return self._repr_struct(self.__dict__)