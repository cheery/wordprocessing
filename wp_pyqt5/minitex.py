# This is fourth rewrite of the MiniTeX that I wrote 4 years ago.
# There's a blogpost about that one in my blog.

class Box(object):
    def __init__(self, width, height, depth, paint=None):
        self.paint = paint
        self.width = width
        self.height = height
        self.depth = depth
        self.shift = 0
        self.offset = 0

class Glue(object):
    def __init__(self, width, shrink=0, stretch=0, paint=None):
        self.paint = paint
        self.width = width
        self.shrink = shrink
        self.stretch = stretch
        self.computed = 0
        self.offset = 0

class Frame(object):
    def __init__(self, width, height, depth, contents, layout, paint=None):
        self.paint = paint
        self.width = width
        self.height = height
        self.depth = depth
        self.shift = 0
        self.offset = 0
        self.contents = contents
        self.layout = layout

# Hints are acknowledged during layouting.
# Box building procedures remove them though.
class Hint(object):
    def __init__(self, node, name, arg):
        self.node = node
        self.name = name
        self.arg = arg

def get_hint(node, name, default=None):
    while isinstance(node, Hint) and node.name != name:
        node = node.node
    if isinstance(node, Hint):
        return node.arg
    else:
        return default

def strip(node):
    while isinstance(node, Hint):
        node = node.node
    return node

# On top-down pass elements will be chosen.

# The routine building the boxes may be made from lists or generators.
# This is accomodated with a folding routine.
def fold(contents):
    for item in contents:
        if isinstance(item, (Frame,Box,Glue,Hint)):
            yield item
        else:
            for deep_item in fold(item):
                yield deep_item

# If you want restricted horizontal/vertical mode.
# You can use hpack/vpack directly.

# Imitation of vertical modes
def vmode(contents, line_break, align, page_width):
    nodes = []
    paragraph = []
    for node in contents:
        if get_hint(node, 'vertical', False):
            if len(paragraph) > 0:
                nodes.extend(line_break(paragraph, align, page_width))
                paragraph = []
            nodes.append(get_hint(node, 'v-rep', node))
        else:
            paragraph.append(node)
    if len(paragraph) > 0:
        nodes.extend(line_break(paragraph, align, page_width))
    return vpack(nodes)

def no_line_break(paragraph, align, page_width):
    yield align(paragraph, True, page_width)

#def line_break_greedy(paragraph, env):
#    indent = 0
#    line = []
#    remaining = env.page_width
#    breakpoint = 0
#    for box in paragraph:
#        if remaining < box.width and breakpoint > 0:
#            lineseg = hpack(line[:breakpoint-1])
#            lineseg.shift = indent
#            yield lineseg
#            line = line[breakpoint:]
#            breakpoint = 0
#            indent = env.indent
#            remaining = env.page_width - sum(box.width for box in line) - indent
#        line.append(box)
#        remaining -= box.width
#        if box.get_hint('break'):
#            breakpoint = len(line)
#    lineseg = hpack(line)
#    lineseg.shift = indent
#    yield lineseg
#
#def line_break_greedy_justify(paragraph, env):
#    indent = 0
#    line = []
#    remaining = env.page_width - indent
#    breakpoint = 0
#    for box in paragraph:
#        if remaining < box.width and breakpoint > 0:
#            lineseg = hpack(line[:breakpoint-1], to_dimen=env.page_width)
#            lineseg.shift = indent
#            yield lineseg
#            line = line[breakpoint:]
#            breakpoint = 0
#            indent = env.indent
#            remaining = env.page_width - sum(box.width for box in line) - indent
#        line.append(box)
#        remaining -= box.width
#        if box.get_hint('break'):
#            breakpoint = len(line)
#    lineseg = hpack(line)
#    lineseg.shift = indent
#    yield lineseg
#

# Somewhat less clumsy implementation of minimum raggedness algorithm.
def line_break(paragraph, text_align, page_width):
#def line_break(paragraph, env):
    length = len(paragraph)
    page_width = page_width
    memo = []
    def penalty_of(index):
        return memo[length - index][0]

    def penalty(cut, width):
        # Adjustment to not penalize final line
        if cut == length and width*10 > page_width:
            return 0
        p = penalty_of(cut)
        if width <= page_width:
            return p + (page_width - width) ** 2
        return 2**10

    def cut_points(start):
        cut = start + 1
        width = strip(paragraph[start]).width
        none_yet = True
        while cut < length and (none_yet or width <= page_width):
            if get_hint(paragraph[cut], 'break'):
                yield width, cut
                none_yet = False
            width += strip(paragraph[cut]).width
            cut += 1
        if cut == length:
            yield width, cut

    def compute(start):
        if start == length:
            return (0, length)
        return min(
            (penalty(cut, width), cut)
            for width, cut in cut_points(start))

    index = length
    while index >= 0:
        memo.append(compute(index))
        index -= 1

    start = 0
    while start < length:
        cut = memo[length - start][1]
        yield text_align(paragraph[start:cut], cut==length, page_width)
        start = cut+1

# Pass into vmode to affect line alignment behavior.
def align_justify(line, is_last_line, page_width):
    if is_last_line:
        return hpack(line)
    return hpack(line, to_dimen=page_width)

def align_left(line, is_last_line, page_width):
    return hpack(line)

def align_right(line, is_last_line, page_width):
    return hpack([hfil()] + line)

def align_center(line, is_last_line, page_width):
    return hpack([hfil()] + line + [hfil()])

# Paragraph break gets line height.
def par(line_height):
    return Hint(Glue(line_height), 'vertical', True)

# Vertical break
def brk():
    return Hint(Glue(0), 'vertical', True)

# Horizontal fill glue.
def hfil():
    return Glue(1, 0, 1+1j)


##import math
## Table layouting
#def table(rows, values={}):
#    def table_fold(env):
#        env = let(env, values)
#        tab = [[list(fold(cell, env)) for cell in row] for row in rows]
#        col = [0 for i in range(max(map(len, tab)))]
#        for row in tab:
#            for i, cell in enumerate(row):
#                col[i] = max(col[i], sum(x.width for x in cell))
#        box = vpack([
#            hpack([hpack(cell, to_dimen=w) for w, cell in zip(col, row)])
#            for row in tab])
#        if len(box) > 0:
#            y = box[len(box)/2].offset
#            if len(box)%2 == 0:
#                y = (y + box[len(box)/2-1].offset) * 0.5
#            box.height += y
#            box.depth -= y
#        yield box
#    return table_fold
#
### Primitive form of pretty printing.
##def codeline(contents):
##    def _codeline(env):
##        env = Environ.let(env, {'depth': env.depth+1})
##        if env.depth > 1:
##            for item in contents:
##                for box in fold(item, env):
##                    yield box
##        else:
##            row = []
##            for item in contents:
##                row.extend(fold(item, env))
##            boxes = list(codeline_break(env.page_width, row, 0))
##            yield vpack(boxes)
##    return _codeline
##
##def codeline_break(width, row, indent):
##    remaining = width
##    best_depth = 10000
##    for box in row:
##        remaining -= box.width
##        #if remaining < 0:
##        best_depth = min(
##            best_depth,
##            box.get_hint('break_depth', 10000))
##    if best_depth >= 10000 or remaining > 0:
##        line = hpack(row)
##        line.shift = indent
##        yield line
##    else:
##        res, shift = [], 0
##        for box in row:
##            if box.get_hint('break_depth') == best_depth:
##                for subline in codeline_break(width-shift, res, indent+shift):
##                    yield subline
##                res, shift = [], 20
##            else:
##                res.append(box)
##        for subline in codeline_break(width-shift, res, indent+shift):
##            yield subline
##

def nl(break_depth):
    return Hint(Glue(0), 'break_depth', break_depth)

def scan_text(text_input, make_text, make_glue, offset):
    mode = 0
    text = []
    for ch in text_input:
        if ch.isspace():
            next_mode = 1
        else:
            next_mode = 0
        if mode != next_mode or (ord(ch) < 32 and ch != '\n'):
            if len(text) > 0:
                textdata = "".join(text)
                yield (make_text,make_glue)[mode==1](textdata, offset)
                offset += len(textdata)
            mode = next_mode
            text = []
        if (ord(ch) < 32 and ch != '\n'):
            yield make_text(ch, offset)
            offset += len(ch)
        else:
            text.append(ch)
    if len(text) > 0:
        yield (make_text,make_glue)[mode==1]("".join(text), offset)

def scan_plaintext(text_input, make_text, offset):
    text = []
    for ch in text_input:
        if ch == "\n":
            if len(text) > 0:
                textdata = "".join(text)
                yield make_text(textdata, offset)
                offset += len(textdata)
            text = []
            yield Hint(Glue(0), 'vertical', True)
            yield make_text("", offset+1)
            offset += len('\n')
        elif ord(ch) < 32:
            if len(text) > 0:
                textdata = "".join(text)
                yield make_text(textdata, offset)
                offset += len(textdata)
            text = []
            yield make_text(ch, offset)
            offset += len(ch)
        else:
            text.append(ch)
    if len(text) > 0:
        yield make_text("".join(text), offset)

# On make_glue, count '\n' to insert 'par' breaks.

# On bottom-up pass the elements will be measured and placed.
def hpack(contents, to_dimen=None, paint=None):
    width = 0
    height = 0
    depth  = 0
    shrink = 0
    stretch = 0
    contents = [strip(node) for node in contents]
    for node in contents:
        node = strip(node)
        width += node.width
        if isinstance(node, (Box,Frame)):
            height = max(height, node.height - node.shift)
            depth = max(depth, node.depth + node.shift)
        if isinstance(node, Glue):
            shrink = sum_dimen(shrink, node.shrink)
            depth = sum_dimen(stretch, node.stretch)
    expand, width = apply_dimen(to_dimen, width, shrink, stretch)
    x = 0
    for node in contents:
        node.offset = x
        if isinstance(node, Glue):
            x += set_dimen(node, expand)
        else:
            x += node.width
    return Frame(width, height, depth, contents, layout=hlayout, paint=paint)

def vpack(contents, to_dimen=None, paint=None):
    width = 0
    vsize = 0
    shrink = 0
    stretch = 0
    contents = [strip(node) for node in contents]
    for node in contents:
        if isinstance(node, (Box,Frame)):
            vsize += node.height + node.depth
            width = max(width, node.width + node.shift)
        elif isinstance(node, Glue):
            vsize += node.width
            shrink = sum_dimen(shrink, node.shrink)
            stretch = sum_dimen(stretch, node.stretch)
    expand, vsize = apply_dimen(to_dimen, vsize, shrink, stretch)
    y = 0
    for node in contents:
        if isinstance(node, Glue):
            node.offset = y
            y += set_dimen(node, expand)
        else:
            node.offset = y + node.height
            y += node.height + node.depth
    return Frame(width, 0, vsize, contents, layout=vlayout, paint=paint)

def padding(frame, left, top, right, bottom, paint=None):
    frame = strip(frame)
    width = frame.width + left + right
    height = frame.height + top
    depth = frame.depth + bottom
    frame.offset = left
    return Frame(width, height, depth, [frame], layout=playout, paint=paint)

# Utility functions for hpack/vpack
# Imaginary part in complex number can be used to prioritize glue.
def sum_dimen(a, b):
    if a.imag == b.imag:
        return a + b.real
    elif a.imag < b.imag:
        return b
    else:
        return a

def apply_dimen(to_dimen, size, shrink, stretch):
    if to_dimen is None:
        return 0, size
    x = to_dimen - size
    if x < 0 and shrink.real > 0:
        x = (x / shrink.real) + (shrink.imag * 1j)
    elif x > 0 and stretch.real > 0:
        x = (x / stretch.real) + (stretch.imag * 1j)
    return x, to_dimen

def set_dimen(glue, expand):
    glue.computed = glue.width
    if expand.real > 0:
        if glue.stretch.imag == expand.imag:
            glue.computed = glue.width + expand.real * glue.stretch.real
    else:
        if glue.shrink.imag == expand.imag:
            glue.computed = glue.width + expand.real * glue.shrink.real
    return glue.computed

# On last top-down pass the elements will be drawn or plotted.
def hlayout(frame,x,y,left,top,right,bottom):
    top = y-frame.height
    bottom = y+frame.depth
    for node in frame.contents:
        x0 = x+node.offset
        if isinstance(node, Glue):
            x1 = x0+node.computed
            yield node, x0, y, x0, top, x1, bottom
        else:
            yield node, x0, y+node.shift, x0, top, x0+node.width, bottom

def vlayout(frame,x,y,left,top,right,bottom):
    left = x
    right = x+frame.width
    y = y - frame.height
    for node in frame.contents:
        y0 = y+node.offset
        if isinstance(node, Glue):
            y1 = y0+node.computed
            yield node, x, y0, left, y0, right, y1
        else:
            yield node, x+node.shift, y0, left, y0-node.height, right, y0+node.depth

def playout(frame,x,y,left,top,right,bottom):
    left = x
    top = y-frame.height
    right = x+frame.width
    bottom = y+frame.depth
    for node in frame.contents:
        x0 = x+node.offset
        yield node, x0, y, left, top, right, bottom



## Pick nearest point.. Hmm.....
#def pick_nearest(box, x, y):
#    def nearest(node, maxdist):
#        near, distance = None, maxdist
#        if isinstance(node, Composite):
#            dx, dy = delta_point_quad(x, y, node.quad)
#            if dx**2 + dy**4 > maxdist:
#                return near, distance
#            for child in node:
#                n, d = nearest(child, distance)
#                if d < distance:
#                    near = n
#                    distance = d
#            return near, distance
#        elif node.subj is not None:
#            dx, dy = delta_point_quad(x, y, node.quad)
#            offset = (x - (node.quad[0] + node.quad[2])*0.5) > 0
#            return (node.subj, node.index + offset), dx**2 + dy**4
#        else:
#            return None, float('inf')
#    return nearest(box, 500**4)[0]
#
#def delta_point_quad(x, y, quad):
#    x0, y0, x1, y1 = quad
#    return min(max(x0, x), x1) - x, min(max(y0, y), y1) - y
