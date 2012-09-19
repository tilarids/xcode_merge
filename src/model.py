from parser import loads


class Project(object):
    def __init__(self, fname):
        self.fname = fname
        self.read_plist(fname)
    def read_plist(self, fname):
        pbxproj = open(fname).read()
        plistNSData, errorMessage = Foundation.NSData.dataWithContentsOfFile_options_error_(fname, Foundation.NSUncachedRead, None)
        self.d, plistFormat, errorMessage = Foundation.NSPropertyListSerialization.propertyListFromData_mutabilityOption_format_errorDescription_(plistNSData, Foundation.NSPropertyListMutableContainers, None, None)
    def write_plist(self, fname):
        pass


if __name__ == '__main__':
    inp = '/tmp/project.pbxproj'
    out = '/tmp/project2.pbxproj'
    proj = Project(inp)
    proj.write_plist(out)