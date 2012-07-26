class Writer(object):
    """
    @role writer
    @requires json
    """
    def __init__(self, json):
        self._json = json

    def write(self, data):
        print self._json.dumps(data, indent=2)


def read(prompt):
    '@role-inst input'
    return raw_input(prompt)


class Hello(object):
    """
    @role hello
    @requires input writer
    """
    def __init__(self, read, writer):
        self._read = read
        self._writer = writer

    def run(self):
        self._writer.write({'Hello': self._read('Who r u?\n')})
