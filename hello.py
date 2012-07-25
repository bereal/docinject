class Writer(object):
    """
    @role writer
    @requires json
    """
    def __init__(self, json):
        self._json = json

    def write(self, data):
        print self._json.dumps(data, indent=2)


class Hello(object):
    """
    @role hello
    @requires writer
    """
    def __init__(self, writer):
        self._writer = writer
        

    def run(self, name):
        self._writer.write({'Hello': name})

if __name__=='__main__':
    import __main__
    import json
    from docinject import Context
    ctx = Context()
    ctx.register_instance('json', json)
    ctx.inject_module(__main__)
    ctx.get_instance('hello').run('world')
