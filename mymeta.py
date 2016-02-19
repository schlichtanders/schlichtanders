import abc
import inspect
from contextlib import contextmanager

# LIFT functionality
# ==================

# variante 1 as Metaclass
# -----------------------
def use_as_needed(func, kwargs):
    meta = inspect.getargspec(func)
    if meta.keywords is not None:
            return func(**kwargs)
    else:
        # not generic super-constructor - pick only the relevant subentries:
        return func(**{k:kwargs[k] for k in kwargs if k in meta.args})

class NotLiftable(RuntimeError):
    pass

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


# variant 2 as class factory
# --------------------------
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


# common lift functionality
# -------------------------

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