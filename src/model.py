from parser import loads
from writer import puts, puts_part
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

    def get_objects(self):
        return self.pbxproj.def_section.get_val("objects")

    def get_build_refs_set(self):
        ret = set()
        sect = self.get_objects()["PBXBuildFile"]
        if sect is None:
            return ret
        for (key, value) in sect.children:
            assert isinstance(key, PLName)
            assert isinstance(value, PLObject)
            ref = value.def_section.get_val("fileRef")
            assert isinstance(ref, PLName)
            ret.add(ref.name)
        return ret

    def get_proj_ref_to_product_dict(self):
        ret = {}
        obj = self.get_objects()["PBXProject"].def_val
        projRefs = obj.def_section.get_val("projectReferences")
        for projRef in projRefs.children:
            pRef = projRef.def_section.get_val("ProjectRef")
            assert isinstance(pRef, PLName)
            pGroup = projRef.def_section.get_val("ProductGroup")
            assert isinstance(pGroup, PLName)
            ret[pRef.name] = pGroup.name
        return ret

    def get_ref_dict(self):
        ret = {}
        sect = self.get_objects()["PBXFileReference"]
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


def _get_product_group(proj, ref):
    proj_refs = proj.get_proj_ref_to_product_dict()
    return proj_refs.get(ref)

def _rename(from_proj, to_proj, from_name, to_name):
    from_proj_group = _get_product_group(from_proj, to_name)
    to_proj_group = _get_product_group(to_proj, from_name)
    if not from_proj_group is None and not to_proj_group is None:
        to_proj.rename_ref(to_proj_group, from_proj_group)
    to_proj.rename_ref(from_name, to_name)

def _fix_project_refs(base, local, other):
    base_proj_to_product = base.get_proj_ref_to_product_dict()
    local_proj_to_product = local.get_proj_ref_to_product_dict()
    other_proj_to_product = other.get_proj_ref_to_product_dict()
    # other_reverse = dict(reversed(item) for item in other_proj_to_product.iteritems())
    # base_reverse = dict(reversed(item) for item in base_proj_to_product.iteritems())
    for local_proj_ref, local_product in local_proj_to_product.iteritems():
        other_product = other_proj_to_product.get(local_proj_ref)
        base_product = base_proj_to_product.get(local_proj_ref)
        if base_product is None:
            # it's something new, pass it
            pass
        else:
            if base_product != local_product:
                _rename(base, local, local_product, base_product)
            if not other_product is None and base_product != other_product:
                _rename(base, other, other_product, base_product)


def fix_refs(base, local, other):
    def get_ref_dict(proj):
        build_refs = proj.get_build_refs_set()
        proj_refs = proj.get_proj_ref_to_product_dict()
        return {key: value for key, value in proj.get_ref_dict().iteritems() if (key in build_refs or key in proj_refs)}

    _fix_project_refs(base, local, other)

    base_refs = get_ref_dict(base)
    local_refs = get_ref_dict(local)
    other_refs = get_ref_dict(other)
    other_reverse = dict(reversed(item) for item in other_refs.iteritems())
    base_reverse = dict(reversed(item) for item in base_refs.iteritems())
    skip_paths = set()
    if len(base_reverse.keys()) != len(base_refs.keys()):
        # TODO: fix duplicates automatically
        print "There are duplicate refs in base file, some file refs were not fixed. Merge result may be incorrect"
        for key, value in base_refs.iteritems():
            key_reverse = base_reverse[value]
            if key != key_reverse:
                print "Duplicate: %s" % puts_part(value)
                skip_paths.add(value)

    if len(other_reverse.keys()) != len(other_refs.keys()):
        # TODO: fix duplicates automatically
        print "There are duplicate refs in remote file, some file refs were not fixed. Merge result may be incorrect"
        for key, value in other_refs.iteritems():
            key_reverse = other_reverse[value]
            if key != key_reverse:
                print "Duplicate: %s" % puts_part(value)
                skip_paths.add(value)

    for local_name, local_path in local_refs.iteritems():
        if local_path in skip_paths:
            print "Skipping '%s' during refs fix" % local_path
            continue
        other_name = other_reverse.get(local_path)
        if other_name is None:
            continue # there is no such path in other
        if other_name != local_name: # ref was changed
            base_name = base_reverse.get(local_path)
            if base_name is None: # file ref was added both to local and other separately
                _rename(local, other, other_name, local_name)
            else: # base was correct, revert
                if base_name != local_name:
                    _rename(base, local, local_name, base_name)
                if base_name != other_name:
                    _rename(base, other, other_name, base_name)


if __name__ == '__main__':
    base = Project('/tmp/project_base.pbxproj')
    local = Project('/tmp/project_local.pbxproj')
    other = Project('/tmp/project_other.pbxproj')
    fix_file_refs(base, local, other)
    local.write_plist('/tmp/project_local2.pbxproj')    
    other.write_plist('/tmp/project_other2.pbxproj')    
