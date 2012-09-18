import Foundation

class Node(object):
    def __init__(self, key, name, parent):
        self.key = key
        self.name = name
        self.parent = parent
        self.children = []

    def add_child(self, key, name):
        n = Node(key, name, self)
        self.children.append(n)
        return n

class PathToken:
    def __init__(self, path):
        self.path = path

def _find_path(root, key):
    def up(node):
        if not node.parent is None:
            ret = up(node.parent)
            ret.append(node.name)
            return ret
        else:
            return [node.name] 
    if root.key == key:
        raise PathToken('/'.join(up(root)))
    else:
        for x in root.children:
            _find_path(x, key)

def find_path(root, key):
    try:
        _find_path(root, key)
    except PathToken as s:
        return s.path

def build_node(plist):
    def _build(root, key):
        for x in plist['objects'][key].get('children', []):
            name = plist['objects'][x].get('name', None)
            # if name == 'OxmlFontCollectionIndexMapping.cpp':
            #     print "Key is %s" % x
            _build(root.add_child(x, name), x)

    root_key = plist['rootObject']
    main_group_key = plist['objects'][root_key]['mainGroup']
    root = Node(root_key, '', None)
    _build(root, main_group_key)
    return root

def sanity_check(pathToPlist):
    plistNSData, errorMessage = Foundation.NSData.dataWithContentsOfFile_options_error_(pathToPlist, Foundation.NSUncachedRead, None)
    plistContents, plistFormat, errorMessage = Foundation.NSPropertyListSerialization.propertyListFromData_mutabilityOption_format_errorDescription_(plistNSData, Foundation.NSPropertyListMutableContainers, None, None)
    names = {}
    root = build_node(plistContents)
    for key in plistContents['objects'].keys():
        if plistContents['objects'][key]['isa'] == 'PBXFileReference':
            name = plistContents['objects'][key].get('name', None)
            if name:
                if name not in names:
                    names[name] = key
                else:
                    dup = names[name]
                    path1 = find_path(root, key)
                    path2 = find_path(root, dup)
                    print "Duplication of %s: [%s] and [%s]" % (name, path1, path2)

if __name__=="__main__":
    import sys
    sanity_check(sys.argv[1])