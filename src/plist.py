# TODO: move out this code to a specific plist library?

class PLBase(object):
    def __init__(self, children):
        self.children = children

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)



class PLName(PLBase):
    def __init__(self, name, comment):
        super(PLName, self).__init__(None)
        self.name = name
        self.comment = comment

    def __repr__(self):
        return u'<%s, %s>' % (self.name, self.comment)
    
    def name(self):
        return self.name

class PLSection(PLBase):
    def __init__(self, name, members):
        super(PLSection, self).__init__(members)
        self.name = name

    def __repr__(self):
        return u'{%s, %s}' % (self.name or 'UNNAMED', self.children)

    def name(self):
        return self.name

    def __getitem__(self, key):
        # TODO: improve performance
        for item in self.children:
            assert isinstance(item, tuple)
            assert isinstance(item[0], PLName)
            if item[0].name == key:
                return item
        return None

    def get_val(self, key):
        item = self[key]
        if not item is None:
            return item[1]

    @property
    def def_val(self):
        if 0 == len(self.children):
            return None
        else:
            return self.children[0][1]

class PLArray(PLBase):
    def __init__(self, values):
        super(PLArray, self).__init__(values)

    def __repr__(self):
        return repr(self.children)

    def __getitem__(self, key):
        # TODO: improve performance
        for item in self.children:
            if isinstance(item, PLName) and item.name == key:
                return item
            if item == key:
                return item
        return None

class PLObject(PLBase):
    def __init__(self, sections):
        super(PLObject, self).__init__(sections)

    def __repr__(self):
        return repr(self.children)

    def __getitem__(self, key):
        # TODO: improve performance
        for item in self.children:
            assert isinstance(item, PLSection)
            if item.name == key:
                return item
        return None

    @property
    def def_section(self):
        if 0 == len(self.children):
            return None
        else:
            return self.children[0]