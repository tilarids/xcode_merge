from parser import loads
from writer import puts
from plist import PLName, PLArray, PLObject, PLSection, PLBase

class Project(object):
    def __init__(self, fname):
        self.fname = fname
        if fname:
            self.read_plist(fname)
    
    def read_plist(self, fname):
        self.pbxproj = loads(open(fname).read())

    def write_plist(self, fname):
        with open(fname, 'w') as f:
            f.write(puts(self.pbxproj))

    def get_ref_dict(self):
        ret = {}
        sect = self.pbxproj.def_section.get_val("objects")["PBXFileReference"]
        if sect is None:
            return ret
        for (key, value) in sect.children:
            assert isinstance(key, PLName)
            assert isinstance(value, PLObject)
            path = value.def_section.get_val("path")
            assert isinstance(path, PLName)
            ret[key.name] = path.name
        return ret

    def rename_ref(self, from_name, to_name):
        def rename(obj):
            if isinstance(obj, PLName) and obj.name == from_name:
                obj.name = to_name
            elif isinstance(obj, tuple):
                for part in obj:
                    rename(part)
            elif isinstance(obj, PLBase) and not obj.children is None:
                for child in obj.children:
                    rename(child)
        rename(self.pbxproj)


def fix_refs(base, local, other):
    base_refs = base.get_ref_dict()
    local_refs = local.get_ref_dict()
    other_refs = other.get_ref_dict()
    other_reverse = dict(reversed(item) for item in other_refs.iteritems())
    base_reverse = dict(reversed(item) for item in base_refs.iteritems())
    for local_name, local_path in local_refs.iteritems():
        other_name = other_reverse.get(local_path)
        if other_name is None:
            continue # there is no such path in other
        if other_name != local_name: # ref was changed
            base_name = base_reverse.get(local_path)
            if base_name is None: # file ref was added both to local and other separately
                other.rename_ref(other_name, local_name)
            else: # base was correct, revert
                if base_name != local_name:
                    local.rename_ref(local_name, base_name)
                if base_name != other_name:
                    other.rename_ref(other_name, base_name)

if __name__ == '__main__':
    base = Project('/tmp/project_base.pbxproj')
    local = Project('/tmp/project_local.pbxproj')
    other = Project('/tmp/project_other.pbxproj')
    fix_refs(base, local, other)
    local.write_plist('/tmp/project_local2.pbxproj')    
    other.write_plist('/tmp/project_other2.pbxproj')    
