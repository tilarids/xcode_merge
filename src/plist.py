class PLName(object):
    def __init__(self, name, comment):
        self.name = name
        self.comment = comment
    def __repr__(self):
        return u'<%s, %s>' % (self.name, self.comment)

class PLSection(object):
    def __init__(self, name, members):
        self.name = name
        self.members = members
    def __repr__(self):
        return u'{%s, %s}' % (self.name or 'UNNAMED', self.members)

class PLArray(object):
    def __init__(self, values):
        self.values = values
    def __repr__(self):
        return repr(self.values)
