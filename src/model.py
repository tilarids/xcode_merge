import CoreFoundation as CF
import Foundation

class Project(object):
    def __init__(self, fname):
        self.fname = fname
        self.read_plist(fname)
    def read_plist(self, fname):
        # plistNSData, errorMessage = Foundation.NSData.dataWithContentsOfFile_options_error_(fname, Foundation.NSUncachedRead, None)
        # self.d, plistFormat, errorMessage = Foundation.NSPropertyListSerialization.propertyListFromData_mutabilityOption_format_errorDescription_(plistNSData, Foundation.NSPropertyListMutableContainers, None, None)

        fileURL = CF.CFURLCreateFromFileSystemRepresentation(None, fname, len(fname), False)
        ok, resourceData, properties, errorCode = CF.CFURLCreateDataAndPropertiesFromResource(None, fileURL, None, None, None, None)
        self.d, errorCode = CF.CFPropertyListCreateFromXMLData(None, resourceData, CF.kCFPropertyListImmutable, None)

    def write_plist_xml(self, fname):
        fileURL = CF.CFURLCreateFromFileSystemRepresentation(None, fname, len(fname), False)
        stream = CF.CFWriteStreamCreateWithFile(None, fileURL)
        if CF.CFWriteStreamOpen(stream):
            success = CF.CFPropertyListWriteToStream(self.d, stream, CF.kCFPropertyListXMLFormat_v1_0, None);

if __name__ == '__main__':
    inp = '/tmp/project.pbxproj'
    out = '/tmp/project2.pbxproj'
    proj = Project(inp)
    proj.write_plist_xml(out)