import cStringIO as StringIO

from plist import PLName, PLSection, PLArray

class Writer(object):
    def __init__(self, out):
        self.out = out
        self.indent = 0

    def write_indent(self):
        self.out.write('\t' * self.indent)


    def write_name(self, obj):
        self.out.write(obj.name)
        if obj.comment:
            self.out.write(' /* ')
            self.out.write(obj.comment)
            self.out.write(' */')

    def write_section(self, obj):
        long_style = len(obj.members) > 3 or obj.name
        if obj.name:
            self.out.write('\n/* Begin ')
            self.out.write(obj.name)
            self.out.write(' section */\n')
        for (name, value) in obj.members:
            assert isinstance(name, PLName)
            if long_style:
                self.write_indent()
            self.write_name(name)
            self.out.write(' = ')
            self.write_dispatch(value)
            self.out.write(';')
            if long_style:
                self.out.write('\n')
            else:
                self.out.write(' ')
        if obj.name:
            self.out.write('/* End ')
            self.out.write(obj.name)
            self.out.write(' section */')

    def write_array(self, obj):
        long_style = len(obj.values) > 1
        self.out.write("(")
        for value in obj.values:
            self.write_dispatch(value)
            self.out.write(',')
            if long_style:
                self.out.write('\n')
            else:
                self.out.write(' ')
        self.out.write(')')

    def write_object(self, sections):
        long_style = not ( (len(sections) == 1 and len(sections[0].members) < 4))
        self.out.write('{')
        self.indent += 1
        if long_style:
            self.out.write('\n')
        for section in sections:
            assert isinstance(section, PLSection)
            self.write_section(section)
            if long_style:
                self.out.write('\n')
        self.indent -= 1
        if long_style:
            self.write_indent()
        self.out.write('}')

    def write_dispatch(self, obj):
        if isinstance(obj, PLName):
            self.write_name(obj)
        elif isinstance(obj, PLSection):
            self.write_section(obj)
        elif isinstance(obj, PLArray):
            self.write_array(obj)
        elif isinstance(obj, list):
            self.write_object(obj)
        else:
            self.out.write(str(obj))

    def write(self, obj):
        self.out.write("// !$*UTF8*$!\n")
        self.write_dispatch(obj)

def puts(tree):
    out = StringIO.StringIO()
    w = Writer(out)
    w.write(tree)
    ret = out.getvalue()
    out.close()
    return ret

if __name__ == '__main__':
    from parser import *
    try:
        stdin = os.fdopen(sys.stdin.fileno(), 'rb')
        input = stdin.read().decode(ENCODING)
        tree = loads(input)
        print puts(tree)
    except SyntaxError, e:
        msg = (u'syntax error: %s' % e).encode(ENCODING)
        print >> sys.stderr, msg
        sys.exit(1)
