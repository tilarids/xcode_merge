import cStringIO as StringIO

from plist import PLName, PLSection, PLArray, PLObject

class Writer(object):
    def __init__(self, out):
        self.out = out
        self.indent = 0
        self.override_style = None

    def write_indent(self):
        self.out.write('\t' * self.indent)


    def write_name(self, obj):
        self.out.write(obj.name)
        if obj.comment:
            self.out.write(' /* ')
            self.out.write(obj.comment)
            self.out.write(' */')

    def write_section_impl(self, obj, long_style):
        if obj.name:
            self.out.write('\n\n/* Begin ')
            self.out.write(obj.name)
            self.out.write(' section */')
        for (name, value) in obj.children:
            assert isinstance(name, PLName)
            if long_style:
                self.out.write('\n')
                self.write_indent()
            self.write_name(name)
            self.out.write(' = ')
            self.write_dispatch(value)
            self.out.write(';')
            if not long_style:
                self.out.write(' ')
        if obj.name:
            self.out.write('\n/* End ')
            self.out.write(obj.name)
            self.out.write(' section */')

    def write_section(self, obj):
        long_style = len(obj.children) > 3 or obj.name
        if not self.override_style is None:
            long_style = self.override_style
        if obj.name in ["PBXFileReference", "PBXBuildFile"]:
            self.override_style = False
            self.write_section_impl(obj, long_style)
            self.override_style = None
        elif obj.name:
            self.override_style = True
            self.write_section_impl(obj, long_style)
            self.override_style = None
        else:
            self.write_section_impl(obj, long_style)


    def write_array(self, obj):
        long_style = len(obj.children) > 1 or len(obj.children) == 0
        if not self.override_style is None:
            long_style = self.override_style
        self.out.write("(")
        self.indent += 1
        for value in obj.children:
            if long_style:
                self.out.write('\n')
            if long_style:
                self.write_indent()
            self.write_dispatch(value)
            self.out.write(',')
            if not long_style:
                self.out.write(' ')
        self.indent -= 1
        if long_style:
            self.out.write('\n')
            self.write_indent()
        self.out.write(')')

    def write_object(self, obj):
        long_style = not (len(obj.children) == 1 and len(obj.children[0].children) < 4)
        if not self.override_style is None:
            long_style = self.override_style
        self.out.write('{')
        self.indent += 1
        for section in obj.children:
            assert isinstance(section, PLSection)
            self.write_section(section)
        self.indent -= 1
        if long_style:
            self.out.write('\n')
            self.write_indent()
        self.out.write('}')

    def write_dispatch(self, obj):
        if isinstance(obj, PLName):
            self.write_name(obj)
        elif isinstance(obj, PLSection):
            self.write_section(obj)
        elif isinstance(obj, PLArray):
            self.write_array(obj)
        elif isinstance(obj, PLObject):
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
        # stdin = open('/tmp/project.pbxproj', 'rb')
        # out = open('/tmp/project2.pbxproj', 'w')
        input = stdin.read().decode(ENCODING)
        tree = loads(input)
        # w = Writer(out)
        # w.write(tree)
        # out.close()
        print puts(tree)
    except SyntaxError, e:
        msg = (u'syntax error: %s' % e).encode(ENCODING)
        print >> sys.stderr, msg
        sys.exit(1)
