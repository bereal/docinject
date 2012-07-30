import inspect
from itertools import ifilter
try:
    import pygraphviz
except ImportError:
    pygraphviz = None

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

class ConstrNode(object):
    CREATING = object()
    NOT_CREATED = object()
    
    def __init__(self, role, constructor, dependencies, nodes):
        self._constr = constructor
        self._depends = dependencies
        self._nodes = nodes
        self._role = role

    @property
    def instance(self):
        inst = getattr(self, '_instance', self.NOT_CREATED)
        if inst is self.CREATING:
            raise DependencyLoop()

        if inst != self.NOT_CREATED:
            return inst

        self._instance = self.CREATING
        try:
            dep_nodes = (self._nodes[d] for d in self._depends)
            dep_inst = (d.instance for d in dep_nodes)
            self._instance = self._constr(*dep_inst)
        except:
            del self._instance
            raise

        return self._instance
        
    @property
    def depends(self):
        return (self._nodes[d] for d in self._depends)

    def __str__(self):
        return '%s: %s' % (self._role, self._constr.__name__)

class InstNode(object):
    def __init__(self, role, inst):
        self.instance = inst
        self._role = role

    @property
    def depends(self):
        return ()

    def __str__(self):
        return '%s: %s' % (self._role, self.instance.__name__)
        
        

class Context(object):
    CREATING = object()
    NOT_FOUND = object()

    def __init__(self):
        self._nodes = {}

    def __check_free(self, name):
        if name in self._nodes:
            raise RoleOverriding(name)

    def __inject_one(self, item, role, dependencies):
        self.__check_free(role)
        self._nodes[role] = ConstrNode(role, item, dependencies, self._nodes)

    def register_instance(self, name, inst):
        self.__check_free(name)
        self._nodes[name] = InstNode(name, inst)

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
        if role not in self._nodes:
            raise RoleNotFound(role)
        return self._nodes[role].instance

    def export_graph(self, graph=None):
        if graph is None:
            if pygraphviz is None:
                raise Exception("Could not imprort pygraphviz neither graph object is given")
            graph = pygraphviz.AGraph(directed=True)

        for role, node in self._nodes.iteritems():
            name = str(node)
            graph.add_node(name)
            for dep in node.depends:
                graph.add_edge(name, str(dep))

        return graph
