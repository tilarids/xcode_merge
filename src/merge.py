#! /bin/env python
import copy
import difflib
from itertools import izip
import hashlib

from model import Project, fix_refs
from plist import PLName, PLSection, PLObject, PLArray, PLBase
from writer import puts_part


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


class Merger(object):
    def __init__(self):
        self.stacks = [[] for x in xrange(3)]

    def get_path(self, i):
        path = []
        for x in self.stacks[i]:
            if not isinstance(x, PLObject):
                name = get_name(x)
                if not name is None:
                    path.append(name)
        return '::'.join(path)

    def ask(self, mess, verb_mess, *objs):
        ret_options = mess[mess.find('[')+1:mess.find(']')].split('/')
        print mess % tuple("'%s'" % puts_part(x) for x in objs if not x is None),
        print "(you can press 'v' for more verbose mode) ",
        verbosity = 3
        while True:
            inp = raw_input().strip().lower()
            if inp == 'v':
                verbosity += 1
                strs = []
                for i, obj in enumerate(objs):
                    real_v = max(verbosity, len(self.stacks) - 1)
                    if not obj is None:
                        sep = "\n" + '=' * 30 + "\n"
                        s = "\nPath = '%s'\n" % self.get_path(i)
                        s += sep + puts_part(self.stacks[i][-real_v]) + sep
                        strs.append(s)
                print (verb_mess or mess) % tuple(strs),
                print " (you can press 'v' for more verbose mode) ",
            elif not inp in ret_options:
                print "Please select one of the options: [%s]" % '/'.join(ret_options)
            else:
                return inp

    def merge_leaf(self, base, local, other):
        if local == other:
            return local
        if base == local:
            # other was changed
            return other
        if base == other:
            # local was changed
            return local
        ret = self.ask("Value conflict. Local version: %s; Remote version: %s; Base: %s. Which one should be used[l/r/b]?",
                       "Some values were changed in both local and remote versions. Local version: %sRemote version: %sBase: %sWhich one should be used[l/r/b]?",
                       base,
                       local,
                       other)
        if ret == 'l':
            return local
        elif ret == 'r':
            return other
        else:
            return base

    def merge_item(self, *args):
        for i, arg in enumerate(args):
            self.stacks[i].append(arg)
        ret = self._merge_item(*args)
        for i, arg in enumerate(args):
            self.stacks[i].pop()
        return ret

    def _merge_item(self, base, local, other):
        # if isinstance(base, tuple) and base[0].name=="C02AC7AE12C3C6330005B517":
        #     import pdb; pdb.set_trace()

        if isinstance(base, tuple):
            assert isinstance(local, tuple)
            assert isinstance(other, tuple)
            return (base[0], self.merge_item(base[1], local[1], other[1]))
        if not isinstance(base, PLBase) or base.children is None:  # leaf
            return self.merge_leaf(base, local, other)

        if type(local) != type(other) or type(local) != type(base):
            # it seems it's a merge between an array and the names
            def upcast(x):
                if isinstance(x, PLArray):
                    return x
                elif isinstance(x, PLName):
                    return PLArray([x])
                else:
                    assert False  # shouldn't get here
            base, local, other = map(upcast, [base, local, other])

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
                    output.append(self.merge_item(base_item, local_item, other_item))
                else: # items were added both in local and other
                    # treat local as base
                    output.append(self.merge_item(local_item, local_item, other_item))

        def process_delete(li, lend, ri, rend):
            for local_item in local.children[li:lend]:
                local_name = get_name(local_item)
                base_item = base[local_name]
                if base_item is None:
                    # something was added locally
                    output.append(local_item)
                else:
                    if local_name in other_names: # it was reordered
                        local_idx = local_names.index(local_name)
                        other_idx = other_names.index(local_name)
                        process_equal(local_idx, local_idx + 1, other_idx, other_idx + 1)
                        continue

                    # it existed in base but wasn't found in remote
                    if base_item == local_item:
                        # it was removed remotely and wasn't changed locally
                        pass
                    else:
                        # it was removed remotely but was changed locally
                        ret = self.ask("Item was changed locally but remotely deleted. Base: %s; Local: %s. Should we keep the changed local version [y/n]?",
                                       "Item was changed locally but remotely deleted. Base:%sLocal:%sShould we keep the changed local version [y/n]?",
                                       base_item,
                                       local_item,
                                       None)
                        if ret == 'y':
                            output.append(local_item)

        def process_insert(li, lend, ri, rend):
            for other_item in other.children[ri:rend]:
                other_name = get_name(other_item)
                base_item = base[other_name]
                if base_item is None:
                    # something was added remotely
                    output.append(other_item)
                else:
                    if other_name in local_names:
                        continue # it was reordered, do nothing, everything was done in process_delete
                    # it existed in base but wasn't found in local
                    if base_item == other_item:
                        # it was removed locally and wasn't changed remotely
                        pass
                    else:
                        # it was removed locally but was changed remotely
                        ret = self.ask("Item was changed remotely but locally deleted. Base: %s; Remote: %s. Should we keep the changed remote version [y/n]?",
                                       "Item was changed remotely but locally deleted. Base:%sRemote:%sShould we keep the changed remote version [y/n]?",
                                       base_item,
                                       None,
                                       other_item)
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

    def merge(self, base, local, other):
        output = Project(None)
        output.pbxproj = self.merge_item(base.pbxproj, local.pbxproj, other.pbxproj)
        return output


def merge(base, local, other):
    fix_refs(base, local, other)
    merger = Merger()
    return merger.merge(base, local, other)

if __name__ == '__main__':
    # base = Project('/tmp/project_other.pbxproj')
    # local = Project('/tmp/project_other.pbxproj')
    # other = Project('/tmp/project_output.pbxproj')
    # base = Project('/tmp/project_base.pbxproj')
    # local = Project('/tmp/project_local.pbxproj')
    # other = Project('/tmp/project_other.pbxproj')
    # base = Project('/tmp/qp_base.pbxproj')
    # local = Project('/tmp/qp_feb.pbxproj')
    # other = Project('/tmp/qp_apr.pbxproj')
    import sys
    base = Project(sys.argv[1])
    local = Project(sys.argv[2])
    other = Project(sys.argv[3])
    output = merge(base, local, other)
    # output.write_plist('/tmp/output.pbxproj')
    output.write_plist(sys.argv[4])
    # output.write_plist('/tmp/qp_output.pbxproj')
