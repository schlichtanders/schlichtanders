from types import MethodType
from collections import defaultdict


class Listenable(object):
    _listeners = None
    
    def add_listener(self, attr, listener_id, listener):
        """ adds listener
        :param listener: function
        :param listener_id: should be unique hashable identifier (used for again deleting the listener)
        """
        if self._listeners is None:
            self._listeners = defaultdict(dict) # or maybe OrderedDict?? dict is faster
        self._listeners[attr][listener_id] = listener
    
    def remove_listener(self, listener_id, attr=None):
        if self._listeners is None:
            return
        if attr is not None:
            del self._listeners[attr][listener_id]
        else:
            for dictionary in self._listeners.itervalues():
                if dictionary.has_key(listener_id):
                    del dictionary[listener_id]
        
    def __getattribute__(self, name):
        s = super(Listenable, self).__getattribute__(name)
        _listeners = object.__getattribute__(self, "_listeners")
        if _listeners and name in _listeners:
            if isinstance(s, MethodType):
                #TODO add decorator wrapper of functools
                def wrapper(*args, **kwargs):
                    result = s(*args, **kwargs)
                    for listener in _listeners[name].itervalues():
                        listener(result) # notify with method result
                    return result
                return wrapper
            else: # else always normal attribute hopefully
                for listener in _listeners[name].itervalues():
                    listener() # just notify it
        return s