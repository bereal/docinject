import inspect
from itertools import ifilter

def parse_doc(s):
    result = {}
    
    for line in (l.strip() for l in s.splitlines()):
        if not line: continue
        
        words = iter(line.split())
        first = words.next()
        if first.startswith('@'):
            for word in words:
                names = (w.strip() for w in word.split(','))
                result.setdefault(first, []).extend(ifilter(None, names))

    return result

class RoleOverriding(Exception): pass
class RoleNotFound(Exception): pass
class DependencyLoop(Exception): pass

class Context(object):
    CREATING = object()
    NOT_FOUND = object()
    
    def __init__(self):
        self._roles = {}
        self._instances = {}

    def __check_free(self, name):
        if name in self._roles:            
            raise RoleOverriding(name)
    
    def __inject_one(self, item, role, dependencies):
        self.__check_free(role)
        self._roles[role] = (item, dependencies)
        
    def register_instance(self, name, inst):
        self.__check_free(name)
        self._instances[name] = inst
        self._roles[name] = inst
        
    def inject_item(self, item, role=None, dependencies=(), enforce=True):
        if role:
            self.__inject_one(item, role, dependencies)
            return True
        
        doc = getattr(item, '__doc__', '')
        attrs = parse_doc(doc)
        roles = attrs.get('@role', ())
        role_inst = attrs.get('@role-inst', ())
        if not (role_inst or roles):
            if enforce:
                raise RoleNotFound(item)
            return False

        dependencies = attrs.get('@requires', ())
        for r in roles:
            self.__inject_one(item, r, dependencies)

        for r in role_inst:
            self.register_instance(r, item)

    def inject_module(self, module):
        modname = module.__name__
        for name, item in inspect.getmembers(module):
            try:
                if item.__module__ != modname:
                    continue
            except AttributeError:
                continue

            self.inject_item(item, enforce=False)

    def get_instance(self, role):
        if role not in self._roles:
            raise RoleNotFound(role)
        
        existing = self._instances.get(role, self.NOT_FOUND)
        if existing is self.CREATING:
            raise DependencyLoop()

        if existing is not self.NOT_FOUND:
            return existing

        self._instances[role] = self.CREATING
        constr, dependencies = self._roles[role]
        try:
            dep_inst = [self.get_instance(dep) for dep in dependencies]
            inst = constr(*dep_inst)
            self._instances[role] = inst
            return inst
        except:
            del self._instances[role]
            raise
