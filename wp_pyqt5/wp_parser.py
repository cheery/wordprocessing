from collections import namedtuple
from functools import partial

# This is a generated LR0 grammar
# python parsergen4.py ../wordprocessing/grammar.txt
#        -p -o ../wordprocessing/wp_parser2_tables.py --lr0
symtab = ['AT', 'LB', 'LP', 'RB', 'RP', 'SEP', 'TA', 'TEXT', 'element', 'block', 'attribute', 'location']
rtab = [ (12, [True]),
         (8, [True]),
         (8, [True, False]),
         (8, [True, False]),
         (8, [True, False]),
         (9, [False]),
         (9, [True, True]),
         (10, [False]),
         (10, [False, True]),
         (10, [True, False]),
         (10, [True, False, True]),
         (11, [False]),
         (11, [True, True, False]),
         (11, [True, True]),
         (11, [True, False])]
state = [ [2, 1, 3,  0,  0,  0,   0, -2, -1, 0, 0, 0],
          [2, 1, 3, -6,  0,  0,   0, -2, 4, -3, 0, 0],
          [0, 0, 7,  0,  0,  6, -12,  5, 0, 0, 0, -5],
          [0, 0, 0,  0, -8,  9,   0,  8, 0, 0, -4, 0],
          [2, 1, 3, -6,  0,  0,   0, -2, 4, -7, 0, 0],
          [0, 0, 7,  0,  0,  6, -12,  5, 0, 0, 0, -14],
          [0, 0, 7,  0,  0,  6, -12,  5, 0, 0, 0, -15],
          [0, 0, 0,  0, -8,  9,   0,  8, 0, 0, 10, 0],
          [0, 0, 0,  0, -9, 11,   0,  0, 0, 0, 0, 0],
          [0, 0, 0,  0, -8,  9,   0,  8, 0, 0, -10, 0],
          [0, 0, 7,  0,  0,  6, -12,  5, 0, 0, 0, -13],
          [0, 0, 0,  0, -8,  9,   0,  8, 0, 0, -11, 0]]

# Control character table
ctrtab = {
    0x10: 2, # ctrl-P, DLE, 'LP'
    0x11: 4, # ctrl-Q, DC1, 'RP'
    0x12: 1, # ctrl-R, DC2, 'LB'
    0x13: 3, # ctrl-S, DC3, 'RB'
    0x14: 0, # ctrl-T, DC4, 'AT'
    0x15: 6, # ctrl-U, NAK, 'TA'
    0x16: 5} # ctrl-V, SYN, 'SEP'

# Emergency exits are used if input ends up being incomplete
def compute_emergency_exits():
    exits = [-1] * len(state)
    for i in range(len(state)):
        best = -1
        score = -1
        for k in range(len(symtab)):
            if state[i][k] < 0:
                rule = -1-state[i][k]
                thisscore = len(rtab[rule][1])-1
                if (best == -1) or (thisscore >= score and rule < best):
                    best = k
                    score = thisscore
        exits[i] = best
        assert score <= 1 # Implement correct algorithm if higher scores detected.
    # As long as scores are low, like 0,1, they wouldn't improve
    # from further processing.
    return exits

emergency_exits = compute_emergency_exits()

Lexeme = namedtuple("Lexeme", [
    'offset', 'length', 'group', 'text', 'emergency_shit'])
Element = namedtuple("Element", [
    'offset', 'length', 'group', 'rule', 'contents', 'emergency_shit'])

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
        lex.fn(Lexeme(lex.offset, len(text), 7, text, False))
        lex.buf = []
        lex.offset = lex.offset + len(text)
    if mode == 7:
        lex.buf.append(ch)
    else:
        lex.fn(Lexeme(lex.offset, len(ch), mode, ch, False))
        lex.offset = lex.offset + len(ch)

def lex_done(lex):
    if len(lex.buf) > 0:
        text = "".join(lex.buf)
        lex.fn(Lexeme(lex.offset, len(text), 7, text, False))
        lex.buf = []
        lex.offset = lex.offset + len(text)

# Parsing
class PState:
    def __init__(self, offset, fn):
        self.lex = LexState(offset, partial(shift, self))
        self.stack = (None, 0)
        self.fn = fn

def shift(pas, obj):
    stack = pas.stack
    action = state[stack[1]][obj.group]
    # If things break here, we should actually put this into search mode.
    # Do fix-sequence or a panic step.
    #assert action != 0
    while action < 0:
        top = (stack, obj)
        rule = (-1-action)
        if rule == 0:
            action = 0
        else:
            emergency_shit = False
            group = rtab[rule][0]
            contents = []
            offset = obj.offset
            length = obj.length
            for capflag in rtab[rule][1]:
                stack, expr = top
                top = stack[0]
                if capflag:
                    contents.append(expr)
                emergency_shit |= expr.emergency_shit
                length += offset - expr.offset
                offset = expr.offset
            contents.reverse()
            slide(contents, -offset)
            obj = Element(offset, length, group, rule, contents, emergency_shit)
            action = state[stack[1]][group]
    if action == 0:
        pas.stack = (None, 0)
        pas.fn(obj)
    else:
        pas.stack = ((stack, obj), action)

# Used to slide content offsets so they're relative to the element's offset.
def slide(contents, delta):
    for i in range(len(contents)):
        obj = contents[i]
        if isinstance(obj, Lexeme):
            obj = Lexeme(obj.offset+delta, obj.length,
                obj.group, obj.text, obj.emergency_shit)
        elif isinstance(obj, Element):
            obj = Element(obj.offset+delta, obj.length,
                obj.group, obj.rule, obj.contents, obj.emergency_shit)
        contents[i] = obj

def panic_excretion(pas):
    while pas.stack[0] != None:
        group = emergency_exits[pas.stack[1]]
        if group < 8:
            obj = Lexeme(pas.lex.offset, 0, group, "", True)
        else:
            obj = Element(pas.lex.offset, 0, group, -1, [], True)
        shift(pas, obj)

# The interface to this module.
def parse_text(pas, text):
    lex_text(pas.lex, text)

def parse_done(pas):
    lex_done(pas.lex)
    panic_excretion(pas)

if __name__=='__main__':
    def fook(element):
        print(element)
    pas = PState(0, fook)
    with open("../sample_text.wp", 'r') as fd:
        parse_text(pas, fd.read())
    parse_done(pas)
