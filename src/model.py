from parser import loads
from writer import puts

class Project(object):
    def __init__(self, fname):
        self.fname = fname
        self.read_plist(fname)
    def read_plist(self, fname):
        self.pbxproj = loads(open(fname).read())
    def write_plist(self, fname):
        with open(fname, 'w') as f:
            f.write(puts(self.pbxproj))


if __name__ == '__main__':
    inp = '/tmp/project.pbxproj'
    out = '/tmp/project2.pbxproj'
    proj = Project(inp)
    proj.write_plist(out)