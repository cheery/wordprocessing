from collections import namedtuple
from functools import partial

# This is a generated LR0 grammar
# python parsergen4.py ../wordprocessing/grammar.txt
#        -p -o ../wordprocessing/wp_parser2_tables.py --lr0
symtab = ['LB', 'LP', 'RB', 'RP', 'SEP', 'TEXT', 'element', 'block', 'attribute']
rtab = [ (9, [True]),
  (6, [True]),
  (6, [True, False]),
  (6, [True, False]),
  (7, [False]),
  (7, [True, True]),
  (8, [False]),
  (8, [False, True]),
  (8, [True, False]),
  (8, [True, False, True])]
state = [ [1, 2, 0, 0, 0, -2, -1, 0, 0],
  [1, 2, -5, 0, 0, -2, 3, -3, 0],
  [0, 0, 0, -7, 5, 4, 0, 0, -4],
  [1, 2, -5, 0, 0, -2, 3, -6, 0],
  [0, 0, 0, -8, 6, 0, 0, 0, 0],
  [0, 0, 0, -7, 5, 4, 0, 0, -9],
  [0, 0, 0, -7, 5, 4, 0, 0, -10]]

# Control character table
ctrtab = {
    0x10: 2, # ctrl-P, DLE, 'LP'
    0x11: 4, # ctrl-Q, DC1, 'RP'
    0x12: 1, # ctrl-R, DC2, 'LB'
    0x13: 3, # ctrl-S, DC3, 'RB'
    # 0x14: 0, # ctrl-T, DC4, 'AT'
    # 0x15: 6, # ctrl-U, NAK, 'TA'
    0x16: 5} # ctrl-V, SYN, 'SEP'

Text = namedtuple("Text", [
    'offset', 'length', 'group', 'text'])
Element = namedtuple("Element", [
    'offset', 'length', 'group', 'rule', 'contents'])

# Lexical analysis
class LexState:
    def __init__(self, offset, fn):
        self.buf = []
        self.offset = offset
        self.fn = fn

def lex_text(lex, text):
    for ch in text:
        lex_char(lex, ch)

def lex_char(lex, ch):
    mode = ctrtab.get(ord(ch), 7)
    if mode != 7 and len(lex.buf) > 0:
        text = "".join(lex.buf)
        lex.fn(Text(lex.offset, len(text), 7, text))
        lex.buf = []
        lex.offset = lex.offset + len(text)
    if mode == 7:
        lex.buf.append(ch)
    else:
        lex.fn(Text(lex.offset, len(ch), mode, ch))
        lex.offset = lex.offset + len(ch)

def lex_done(lex):
    if len(lex.buf) > 0:
        text = "".join(lex.buf)
        lex.fn(Text(lex.offset, len(text), 7, text))
        lex.buf = []
        lex.offset = lex.offset + len(text)

# Parsing
class PState:
    def __init__(self, offset, fn):
        self.failsafe = []
        self.lex = LexState(offset, partial(shift, self))
        self.stack = (None, 0)
        self.fn = fn

def shift(pas, obj):
    stack = pas.stack
    action = state[stack[1]][obj.group]
    # If things break here, we take the failsafe and use it.
    if action == 0:
        include_obj = (state[0][obj.group] == 0)
        if include_obj:
            pas.failsafe.append(obj)
        offset = pas.failsafe[0].offset
        length = pas.failsafe[-1].offset + pas.failsafe[-1].length - offset
        slide(pas.failsafe, -offset)
        pas.fn(Element(offset, length, 8, 0, pas.failsafe))
        pas.failsafe = []
        if include_obj:
            return
    else:
        pas.failsafe.append(obj)
    while action < 0:
        top = (stack, obj)
        rule = (-1-action)
        if rule == 0:
            action = 0
        else:
            group = rtab[rule][0]
            contents = []
            offset = obj.offset
            length = obj.length
            for capflag in rtab[rule][1]:
                stack, expr = top
                top = stack[0]
                if capflag:
                    contents.append(expr)
                length += offset - expr.offset
                offset = expr.offset
            contents.reverse()
            slide(contents, -offset)
            obj = Element(offset, length, group, rule, contents)
            action = state[stack[1]][group]
    if action == 0:
        pas.stack = (None, 0)
        pas.fn(obj)
        pas.failsafe = []
    else:
        pas.stack = ((stack, obj), action)

# Used to slide content offsets so they're relative to the element's offset.
def slide(contents, delta):
    for i in range(len(contents)):
        obj = contents[i]
        if isinstance(obj, Text):
            obj = Text(obj.offset+delta, obj.length,
                obj.group, obj.text)
        elif isinstance(obj, Element):
            obj = Element(obj.offset+delta, obj.length,
                obj.group, obj.rule, obj.contents)
        contents[i] = obj

# The interface to this module.
def parse_text(pas, text):
    lex_text(pas.lex, text)

def parse_done(pas):
    lex_done(pas.lex)
    if len(pas.failsafe) > 0:
        offset = pas.failsafe[0].offset
        length = pas.failsafe[-1].offset + pas.failsafe[-1].length - offset
        slide(pas.failsafe, -offset)
        pas.fn(Element(offset, length, 8, 0, pas.failsafe))
        pas.failsafe = []


if __name__=='__main__':
    import argparse
    apa = argparse.ArgumentParser(description="Try out the parser")
    apa.add_argument('filename', type=str)
    args = apa.parse_args()
    def fook(element):
        print(element)
    pas = PState(0, fook)
    with open(args.filename, 'r') as fd:
        parse_text(pas, fd.read())
    parse_done(pas)
