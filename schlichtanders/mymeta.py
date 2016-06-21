import abc
from contextlib import contextmanager
from .myfunctools import use_as_needed
import wrapt
import inspect
from functools import partial
import inspect
from collections import defaultdict

"""
make one object like another
============================
different versions of inplace-copy
"""


def morph(instance1, instance2):
    """ makes instance1 to be instance2, however works inplace, i.e. preserves all references to instance1 """
    instance1.__class__ = instance2.__class__
    instance1.__dict__ = instance2.__dict__
    return instance1  # just for convenience, if needed


# Proxy:

"""
The following proxy is an alternative to pyjack.replace_all_refs. It looks almost identical in use.
Difference? the proxy could be adapted to have extra functionalities (see https://pypi.python.org/pypi/ProxyTypes/0.9)
the pyjack.replace_all_refs might fail with weakrefs or other fancy stuff... don't know.

Indeed a first test showed that pyjack.replace_all_refs does not works perfect...
"""


def proxify(a, b):
    """ makes a a proxy for b, in place """
    if isinstance(a, Proxifier):
        a = get_subject(a)
    if isinstance(b, Proxifier):
        b = get_subject(b)
    if a == b:  # otherwise infinte loops occur
        return a
    # else
    old_class, old_dict = a.__class__, a.__dict__
    a.__class__ = Proxifier
    Proxifier.__init__(a, b, old_class, old_dict)
    return a


def get_subject(a):
    """ returns the final subject of possible several proxy layers """
    if hasattr(a, "__subject__"):
        return get_subject(a.__subject__)
    else:
        return a


class Proxifier(object):
    # taken from https://pypi.python.org/pypi/ProxyTypes/0.9
    # modifed such that it does not use __slot__ and that it has __original__

    """ Delegates all operations (except ``.__subject__, .__original__``) to another object

    ``__original__`` returns a new instance of the originally proxified object
    """

    def __init__(self, subject, old_class, old_dict):
        self.__old_class__ = old_class
        self.__old_dict__ = old_dict
        self.__subject__ = subject

    def __call__(self,*args,**kw):
        return self.__subject__(*args,**kw)

    def __getattribute__(self, attr, oga=object.__getattribute__):
        if attr in ('__subject__', '__old_class__', '__old_dict__'):
            return oga(self, attr)
        if attr == '__original__':
            old_class = oga(self, '__old_class__')
            old_dict = oga(self, '__old_dict__')
            proxified = old_class.__new__(old_class)
            proxified.__dict__ = old_dict
            return proxified
        subject = oga(self, '__subject__')
        return getattr(subject, attr)

    def __setattr__(self,attr,val, osa=object.__setattr__):
        if attr in ('__subject__', '__old_class__', '__old_dict__'):
            osa(self,attr,val)
        else:
            setattr(self.__subject__,attr,val)

    def __delattr__(self,attr, oda=object.__delattr__):
        if attr in ('__subject__', '__old_class__', '__old_dict__'):
            oda(self, attr)
        else:
            delattr(self.__subject__,attr)

    def __nonzero__(self):
        return bool(self.__subject__)

    def __getitem__(self,arg):
        return self.__subject__[arg]

    def __setitem__(self,arg,val):
        self.__subject__[arg] = val

    def __delitem__(self,arg):
        del self.__subject__[arg]

    def __getslice__(self,i,j):
        return self.__subject__[i:j]


    def __setslice__(self,i,j,val):
        self.__subject__[i:j] = val

    def __delslice__(self,i,j):
        del self.__subject__[i:j]

    def __contains__(self,ob):
        return ob in self.__subject__

    for name in 'repr str hash len abs complex int long float iter oct hex'.split():
        exec "def __%s__(self): return %s(self.__subject__)" % (name,name)

    for name in 'cmp', 'coerce', 'divmod':
        exec "def __%s__(self,ob): return %s(self.__subject__,ob)" % (name,name)

    for name,op in [
        ('lt','<'), ('gt','>'), ('le','<='), ('ge','>='),
        ('eq','=='), ('ne','!=')
    ]:
        exec "def __%s__(self,ob): return self.__subject__ %s ob" % (name,op)

    for name,op in [('neg','-'), ('pos','+'), ('invert','~')]:
        exec "def __%s__(self): return %s self.__subject__" % (name,op)

    for name, op in [
        ('or','|'),  ('and','&'), ('xor','^'), ('lshift','<<'), ('rshift','>>'),
        ('add','+'), ('sub','-'), ('mul','*'), ('div','/'), ('mod','%'),
        ('truediv','/'), ('floordiv','//')
    ]:
        exec (
            "def __%(name)s__(self,ob):\n"
            "    return self.__subject__ %(op)s ob\n"
            "\n"
            "def __r%(name)s__(self,ob):\n"
            "    return ob %(op)s self.__subject__\n"
            "\n"
            "def __i%(name)s__(self,ob):\n"
            "    self.__subject__ %(op)s=ob\n"
            "    return self\n"
        )  % locals()

    del name, op

    # Oddball signatures

    def __rdivmod__(self,ob):
        return divmod(ob, self.__subject__)

    def __pow__(self,*args):
        return pow(self.__subject__,*args)

    def __ipow__(self,ob):
        self.__subject__ **= ob
        return self

    def __rpow__(self,ob):
        return pow(ob, self.__subject__)

"""
class tree helpers
==================
"""

def clcoancl(*cls_list):
    """ read as closest common ancestor class
    taken from: http://stackoverflow.com/questions/15788725/how-to-determine-the-closest-common-ancestor-class"""
    mros = [list(inspect.getmro(cls)) for cls in cls_list]
    track = defaultdict(int)
    while mros:
        for mro in mros:
            cur = mro.pop(0)
            track[cur] += 1
            if track[cur] == len(cls_list):
                return cur
            if len(mro) == 0:
                mros.remove(mro)
    return None  # or raise, if that's more appropriate

"""
LIFT functionality
==================
"""

class NotLiftable(TypeError):
    pass

"""
variant 0 as static function decorator
--------------------------------------
"""
# TODO include into generic lift function?

def lift_from(*classes):
    """ shall decorate class method ideally
    >>> class A(object):
    ...     pass
    ...
    >>> class B(A):
    ...     @lift_from(A)
    ...     @staticmethod
    ...     def lift(a,_b):
    ...         a.__class__ = B
    ...         a._b = _b
    ...
    >>> class C(B):
    ...     def __init__(self, _c):
    ...         self._c = _c
    ...
    ...     @lift_from(B)
    ...     @staticmethod
    ...     def lift(b, _c):
    ...         b.__class__ = C
    ...         b._c = _c
    ...
    ...     def __str__(self):
    ...         return "%s(_b=%s,_c=%s)" % (self.__class__.__name__, self._b, self._c)
    ...
    >>> a = A()
    >>> C.lift(a, _b="b", _c="c")
    >>> print a
    C(_b=b,_c=c)
    """
    @wrapt.decorator
    def wrapper(lift, instance, args, kwargs):
        to_lift = args[0]

        if not isinstance(to_lift, classes):
            for c in classes:
                if hasattr(c, "lift"):
                    try:
                        use_as_needed(c.lift, kwargs, args=[to_lift])  # preprocess lift
                        break
                    except NotLiftable:
                        pass
            else:
                raise NotLiftable("Not liftable from class %s" % to_lift.__class__)
        # final lift:
        return use_as_needed(lift, kwargs, args=args) #args are only applied to direct lift
    return wrapper


"""
variante 1 as Metaclass
-----------------------
"""

@contextmanager
def super_liftable(cls, self):
    """ this is kind of a hack to replace super.super, however I haven't found any other nice way to do it """
    if cls is object:
        raise NotLiftable()
    liftables = [l for l in cls.__bases__ if type(l).__name__ == "Liftable"]
    if not liftables:
        raise NotLiftable()
        
    orig_class = self.__class__
    self.__class__ = liftables[0]
    yield self
    self.__class__ = orig_class

    
def LiftableFrom(base_cls_name):
    
    class Liftable(abc.ABCMeta):
        def __init__(cls, name, bases, dct):
            # for base_cls nothing should be done, as this is the one to refer to by Lifting
            if not cls.__name__ == base_cls_name:
                if "__init__" in dct:
                    raise TypeError("Descendents of Liftable are not allowed to have own __init__ method. Instead overwrite __initialize__")
                
                def lifted__init__(self, **kwargs):
                    with super_liftable(cls, self) as s:
                        use_as_needed(s.__init__, kwargs)
                    if hasattr(self, "__initialize__"):
                        use_as_needed(self.__initialize__, kwargs)

                cls.__init__ = lifted__init__
                #setattr(cls, "__init__", lifted__init__)
                
            super(Liftable, cls).__init__(name, bases, dct)
    
    Liftable.base_cls_name = base_cls_name
    #Liftable.__name__ = "LiftableFrom" + base_cls_name   # to show that this is possible
    return Liftable

"""
variant 2 as class factory
--------------------------
"""

@contextmanager
def mysuper(cls, self):
    orig_class = self.__class__
    self.__class__ = cls
    yield self
    self.__class__ = orig_class
    
def Lift(cls):
    """ class decorator """
    class _Lift(cls):
        __metaclass__ = abc.ABCMeta
        
        def __init__(self, **kwargs):
            with mysuper(cls, self) as s:
                use_as_needed(s.__init__, kwargs)
#             #TODO the following does not work, but would be the first thing to try
#             #gives TypeError: <method-wrapper '__init__' of C object at 0x7f0ee504a610> is not a Python function
#             #i.e. super(cls, self).__init__ is not an inspectable function as one would expect
#             use_as_needed(super(cls, self).__init__, kwargs) 
            use_as_needed(self.__initialize__, kwargs)
        
        @abc.abstractmethod
        def __initialize__(self, **kwargs):
            return NotImplemented()
    
    _Lift.__name__ = "_Lift_" + cls.__name__
    return _Lift

"""
common lift functionality
-------------------------
"""

def lift(self, new_class, **kwargs):
    # Stop Conditions:
    if self.__class__ is new_class:
        return # nothing to do
    elif new_class is object: # Base Case
        # break recursion at once:
        raise NotLiftable()
    
    liftables = [l for l in new_class.__bases__ if type(l).__name__ == "Liftable"]
    lifts = [l.__base__ for l in new_class.__bases__ if l.__name__.startswith("_Lift_")]
    ls = liftables + lifts
    if not ls:
        raise NotLiftable()

    # recursive case:
    if not self.__class__ is ls[0]: # it would also be possible to use tree like left-first-search here
        lift(self, ls[0], **kwargs)
    # own case:
    self.__class__ = new_class
    if hasattr(self, '__initialize__'):
        use_as_needed(self.__initialize__, kwargs)
    
    
def delift(self, base_class):
    self.__class__ = base_class
    
def next_common_liftable_ancestor(classA, classB):
    a = [c for c in classA.__mro__ if type(c).__name__=='Liftable']
    b = [c for c in classB.__mro__ if type(c).__name__=='Liftable']
    """uses a for order"""
    for i in a:
        if i in b:
            return i

def relift(self, new_class, base_class=None, **kwargs):
    if base_class is None:
        base_class = next_common_liftable_ancestor(self.__class__, new_class)
    delift(self, base_class)
    lift(self, new_class, **kwargs)