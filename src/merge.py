import copy
import difflib
from itertools import izip
import hashlib

from model import Project
from plist import PLName, PLSection, PLObject, PLArray, PLBase

def ask(mess):
    ret_options = mess[mess.find('[')+1:mess.find(']')].split('/')
    print mess," ",
    while True:
        inp = raw_input().strip().lower()
        if not inp in ret_options:
            print "Please select one of the options: [%s]" % '/'.join(ret_options) 
        else:
            return inp

item_name_repr = repr

def merge_leaf(base, local, other):
    if local == other:
        return local
    base_id = item_name_repr(base)
    local_id = item_name_repr(local)
    other_id = item_name_repr(other)
    ret = ask("Value conflict. Local version: %s; Remote version: %s; Base: %s. Which one should be used[l/r/n]?" % (local_id,
                                                                                                                    other_id,
                                                                                                                    base_id))
    if ret == 'l':
        return local
    elif ret == 'r':
        return other
    else:
        return base

def create_item(base, children):
    if isinstance(base, PLSection):
        return PLSection(base.name, children)
    else:
        return base.__class__(children)

def get_name(item):
    if isinstance(item, PLObject): # need to generate a name to merge arrays
        return hashlib.sha224(repr(item)).hexdigest()
    elif isinstance(item, tuple):
        name = item[0].name
    else:
        name = item.name
    return name

def merge_item(base, local, other):
    if isinstance(base, tuple):
        assert isinstance(local, tuple)
        assert isinstance(other, tuple)
        return (base[0], merge_item(base[1], local[1], other[1]))
    if not isinstance(base, PLBase) or base.children is None: # leaf
        return merge_leaf(base, local, other)

    assert type(local) == type(other)
    assert type(local) == type(base)

    local_names = map(get_name, local.children)
    other_names = map(get_name, other.children)

    s = difflib.SequenceMatcher()
    s.set_seqs(local_names, other_names)
    output = []

    def process_equal(li, lend, ri, rend):
        for local_item, other_item in izip(local.children[li:lend],other.children[ri:rend]):
            base_item = base[get_name(local_item)]
            if base_item:
                output.append(merge_item(base_item, local_item, other_item))
            else: # items were added both in local and other
                # treat local as base
                output.append(merge_item(local_item, local_item, other_item))

    def process_delete(li, lend, ri, rend):
        for local_item in local.children[li:lend]:
            base_item = base[get_name(local_item)]
            if base_item is None:
                # something was added locally
                output.append(local_item)
            else:
                # TODO: check if it was reordered
                # it existed in base but wasn't found in remote
                if base_item == local_item:
                    # it was removed remotely and wasn't changed locally
                    pass
                else:
                    # it was removed remotely but was changed locally
                    item_id = item_name_repr(local_item)
                    ret = ask("Item %s was changed locally but remotely deleted. Should we keep the changed local version [y/n]?" % item_id)
                    if ret == 'y':
                        output.append(local_item)

    def process_insert(li, lend, ri, rend):
        for other_item in other.children[ri:rend]:
            base_item = base[get_name(other_item)]
            if base_item is None:
                # something was added remotely
                output.append(other_item)
            else:
                # TODO: check if it was reordered
                # it existed in base but wasn't found in local
                if base_item == other_item:
                    # it was removed locally and wasn't changed remotely
                    pass
                else:
                    # it was removed locally but was changed remotely
                    item_id = item_name_repr(other_item)
                    ret = ask("Item %s was changed remotely but locally deleted. Should we keep the changed remote version [y/n]?" % item_id)
                    if ret == 'y':
                        output.append(other_item)

    for (opcode, li, lend, ri, rend) in s.get_opcodes():
        if opcode == 'equal':
            process_equal(li, lend, ri, rend)
        elif opcode == 'delete':
            process_delete(li, lend, ri, rend)
        elif opcode == 'insert':
            process_insert(li, lend, ri, rend)
        elif opcode == 'replace':
            process_delete(li, lend, ri, ri)
            process_insert(li, li, ri, rend)
        else:
            raise NotImplementedError
    return create_item(base, output)

def merge(base, local, other):
    output = Project(None)
    output.pbxproj = merge_item(base.pbxproj, local.pbxproj, other.pbxproj)
    return output

if __name__ == '__main__':
    base = Project('/tmp/project_base.pbxproj')
    local = Project('/tmp/project_local.pbxproj')
    other = Project('/tmp/project_other.pbxproj')
    output = merge(base, local, other)
    output.write_plist('/tmp/project_output.pbxproj')