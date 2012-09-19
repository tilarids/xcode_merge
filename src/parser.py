import sys, os, re, logging
from re import VERBOSE
from pprint import pformat

from funcparserlib.lexer import make_tokenizer, Spec
from funcparserlib.parser import (maybe, many, eof, skip, fwd, name_parser_vars,
        SyntaxError, oneplus)
from funcparserlib.contrib.common import const, n, op, op_, sometok

from plist import PLName, PLSection, PLArray

ENCODING = 'utf-8'
regexps = {
    'escaped': ur'''
        \\                                  # Escape
          ((?P<standard>["\\/bfnrt])        # Standard escapes
        | (u(?P<unicode>[0-9A-Fa-f]{4})))   # uXXXX
        ''',
    'unescaped': ur'''
        [\x20-\x21\x23-\x5b\x5d-\uffff]     # Unescaped: avoid ["\\]
        ''',
}

re_esc = re.compile(regexps['escaped'], VERBOSE)
re_section = re.compile("\s*Begin (\w+) section\s*")

def tokenize(str):
    'str -> Sequence(Token)'
    specs = [
        Spec('space', r'[ \t\r\n]+'),
        Spec('string', ur'"(%(unescaped)s | %(escaped)s)*"' % regexps, VERBOSE),
        Spec('number', r'''
            -?                  # Minus
            (0|([1-9][0-9]*))   # Int
            (\.[0-9]+)?         # Frac
            ([Ee][+-][0-9]+)?   # Exp
            \b''', VERBOSE),
        Spec('op', r'[{}\(\),;=]'),
        Spec('comment', r'/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/'),
        Spec('name', r'[/.A-Za-z_0-9]+'),
    ]
    useless = ['space']
    t = make_tokenizer(specs)
    return [x for x in t(str) if x.type not in useless]



def make_number(n):
    try:
        return int(n)
    except ValueError:
        return float(n)

def make_section(n):
    assert len(n) == 3

    section_name = n[0]
    if section_name:
        m = re_section.match(section_name)
        if m:
            section_name = m.groups()[0]
    return PLSection(section_name, n[1])

def unescape(s):
    std = {
        '"': '"', '\\': '\\', '/': '/', 'b': '\b', 'f': '\f', 'n': '\n',
        'r': '\r', 't': '\t',
    }
    def sub(m):
        if m.group('standard') is not None:
            return std[m.group('standard')]
        else:
            return unichr(int(m.group('unicode'), 16))
    return re_esc.sub(sub, s)

def make_string(n):
    return unescape(n[1:-1])

def make_comment(n):
    return n[3:-3]

def make_member(n):
    assert len(n) == 2
    return (n[0], n[1])

def make_object(n):
    return n

def make_name(n):
    assert len(n) == 2
    return PLName(n[0], n[1])

def make_array(n):
    return PLArray(n)

number = sometok('number') >> make_number
string = sometok('string') >> make_string
comment = sometok('comment') >> make_comment
name = sometok('name') + maybe(comment) >> make_name

value = fwd()
member = name + op_('=') + value >> make_member
section = maybe(comment) +  oneplus(member + op_(';')) + maybe(comment) >> make_section
object = (
    op_('{') +
    many(section) +
    op_('}')) >> make_object
array = (
    op_('(') +
    many(value + op_(',')) +
    op_(')')) >> make_array
value.define(
      object
    | number
    | string
    | name
    | array)
pbxproj_file = value + skip(eof)

name_parser_vars(locals())

def parse(seq):
    'Sequence(Token) -> object'
    return pbxproj_file.parse(seq)

def loads(s):
    'str -> object'
    return parse(tokenize(s[s.find('\n') + 1:]))

def main():
    logging.basicConfig(level=logging.DEBUG)
    try:
        stdin = os.fdopen(sys.stdin.fileno(), 'rb')
        # stdin = open('/tmp/t2.txt')
        input = stdin.read().decode(ENCODING)
        seq = tokenize(input[input.find('\n') + 1:])
        print pformat(seq)
        tree = loads(input)
        print pformat(tree)
    except SyntaxError, e:
        msg = (u'syntax error: %s' % e).encode(ENCODING)
        print >> sys.stderr, msg
        sys.exit(1)

if __name__ == '__main__':
    main()