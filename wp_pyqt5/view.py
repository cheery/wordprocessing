import paint_qt5
import minitex
import treesitter_dom

def init_dom(buffer):
    rawbuf = b"".join(buffer.peek(0, buffer.length))
    return (buffer, rawbuf, treesitter_dom.parser.parse(rawbuf))

def slice(dom, start, end, text):
    buffer, rb, tree = dom
    start, start_pt = buffer.get_point((0,(0,0)), start)
    old_end  = buffer.get_point((start,start_pt), end)
    count = end-start
    if count > 0:
        buffer.delete(start, count)
    if len(text) > 0:
        s = text.encode('utf-8')
        buffer.insert(start, s)
        count = len(s)
    new_end  = buffer.get_point((start,start_pt), start+count)
    return edit_dom(dom, (start, start_pt), old_end, new_end), count

def edit_dom(dom, start, old_end, new_end):
    # We don't benefit from the piece table at the moment because
    # I can't feed the right reader routine for the treestitter bindings.
    buffer, rb, tree = dom
    #tree.edit(
    #    start_byte=start[0],
    #    old_end_byte=old_end[0],
    #    new_end_byte=new_end[0],
    #    start_point=start[1],
    #    old_end_point=old_end[1],
    #    new_end_point=new_end[1],
    #)
    #rawbuf = b"".join(buffer.peek(0, buffer.length))
    #return (buffer, rawbuf, treesitter_dom.parser.parse(rawbuf, tree))

    # The incremental parsing algorithm
    # seem to have an edge case that it messes up.
    # So can't use that either.

    rawbuf = b"".join(buffer.peek(0, buffer.length))
    return (buffer, rawbuf, treesitter_dom.parser.parse(rawbuf))

def plaintext_display(dom, font):
    buffer, rawbuf, tree = dom
    #elements = []
    #offset = 0
    #pas = wp_parser.PState(offset, elements.append)
    output = []
    #def make_text(ch, offset):
    #    try:
    #        ch = texttab[ch]
    #        return paint_qt5.textbox(font, ch, offset, "#aa88cc")
    #    except KeyError as _:
    #        return paint_qt5.textbox(font, ch, offset)
    #offset = 0
    #for buf in buffer.peek(offset, buffer.length):
    #    text = buf.decode('utf-8')
    #    output.extend(
    #        minitex.scan_plaintext(text, make_text, offset))
    #    #wp_parser.parse_text(pas, text)
    #    offset += len(text)
    ##wp_parser.parse_done(pas)

    cursor = tree.walk()
    render_toplevel(output, rawbuf, cursor, font)
    render_raw(output, rawbuf, cursor, font)

    return minitex.vmode(output,
        minitex.no_line_break,
        minitex.align_left,
        200)

def full_display(dom, monofont, font, getfont):
    buffer, rawbuf, tree = dom
    #rawbuf = b"".join(buffer.peek(0, buffer.length))
    #rawbuf = bytes(src, 'utf8')
    #tree = treesitter_dom.parser.parse(rawbuf)
    cursor = tree.walk()

    # Starts from 0, goes to N
    #print(cursor.node.end_point)

    #print(read_attributes(cursor, rawbuf))

    output = []
    render_toplevel(output, rawbuf, cursor, font)

    return minitex.vmode(output,
        minitex.no_line_break,
        minitex.align_left,
        200)
    #return plaintext_display(buffer, monofont)

def render_toplevel(output, rawbuf, cursor, font):
    for kind in step_children(cursor):
        if kind != "element" and cursor.node.has_error:
            color = "#cc0000"
            if cursor.node.start_byte == cursor.node.end_byte:
                output.extend(
                    scan_plaintext(cursor.node.type, "#00ff00", 
                        cursor.node.start_byte, font))
            else:
                output.extend(
                    scan_plaintext_node(rawbuf, cursor.node, color, font))
        elif cursor.node.type in texttab:
            color = "#aa88cc"
            output.extend(
                scan_plaintext_node(rawbuf, cursor.node, color, font))
        elif cursor.node.type == "attr":
            color = "#0040FF"
            output.extend(
                scan_plaintext_node(rawbuf, cursor.node, color, font))
        elif cursor.node.type == "element":
            if len(read_attributes(cursor, rawbuf)) == 0:
                out = []
                render_paragraph(out, rawbuf, cursor, font)
                output.append(minitex.vmode(out,
                    minitex.line_break,
                    minitex.align_left,
                    paint_qt5.width_of(font, " "*80)))
            else:
                # read_attributes
                #print(read_attributes(cursor, rawbuf))
                render_raw(output, rawbuf, cursor, font)
        else:
            color = "#D0A0D0"
            output.extend(
                scan_plaintext_node(rawbuf, cursor.node, color, font))

def render_paragraph(output, rawbuf, cursor, font):
    for kind in step_children(cursor):
        if kind != "element" and cursor.node.has_error:
            color = "#cc0000"
            if cursor.node.start_byte == cursor.node.end_byte:
                output.extend(
                    scan_plaintext(cursor.node.type, "#00ff00", 
                        cursor.node.start_byte, font))
            else:
                output.extend(
                    scan_plaintext_node(rawbuf, cursor.node, color, font))
        elif cursor.node.type in texttab:
            color = "#aa88cc"
            output.extend(
                scan_plaintext_node(rawbuf, cursor.node, color, font))
        elif cursor.node.type == "attr":
            color = "#0040FF"
            output.extend(
                scan_plaintext_node(rawbuf, cursor.node, color, font))
        elif cursor.node.type == "element":
            render_raw(output, rawbuf, cursor, font)
        else:
            color = "#000000"
            output.extend(
                scan_text_node(rawbuf, cursor.node, color, font))

def render_raw(output, rawbuf, cursor, font):
    for kind in step_children(cursor):
        if kind != "element" and cursor.node.has_error:
            color = "#cc0000"
            if cursor.node.start_byte == cursor.node.end_byte:
                output.extend(
                    scan_plaintext(cursor.node.type, "#00ff00", 
                        cursor.node.start_byte, font))
            else:
                output.extend(
                    scan_plaintext_node(rawbuf, cursor.node, color, font))
        elif cursor.node.type in texttab:
            color = "#aa88cc"
            output.extend(
                scan_plaintext_node(rawbuf, cursor.node, color, font))
        elif cursor.node.type == "attr":
            color = "#0040FF"
            output.extend(
                scan_plaintext_node(rawbuf, cursor.node, color, font))
        elif cursor.node.type == "element":
            render_raw(output, rawbuf, cursor, font)
        else:
            color = "#000000"
            output.extend(
                scan_plaintext_node(rawbuf, cursor.node, color, font))

def step_children(cursor):
    if cursor.goto_first_child():
        yield cursor.node.type
        while cursor.goto_next_sibling():
            yield cursor.node.type
        assert cursor.goto_parent()

def read_attributes(cursor, rawbuf):
    if not cursor.goto_first_child():
        return []
    out = []
    if cursor.node.type == "attr" and not cursor.node.has_error:
        out.append(read_attribute(cursor, rawbuf))
    while cursor.goto_next_sibling():
        if cursor.node.type == "attr" and not cursor.node.has_error:
            out.append(read_attribute(cursor, rawbuf))
    assert cursor.goto_parent()
    return out

def read_attribute(cursor, rawbuf):
    assert cursor.goto_first_child()
    assert cursor.node.type == LP
    out = []
    while cursor.node.type != RP:
        cursor.goto_next_sibling()
        if cursor.node.type == 'text':
            text = (rawbuf[cursor.node.start_byte:cursor.node.end_byte]
                .decode('utf-8'))
            out.append(text)
            assert cursor.goto_next_sibling()
        else:
            out.append("")
    assert cursor.goto_parent()
    return tuple(out)

def scan_plaintext_node(rawbuf, node, color, font):
    def make_text(ch, offset):
        try:
            ch = texttab[ch]
            return paint_qt5.textbox(font, ch, offset, color)
        except KeyError as _:
            return paint_qt5.textbox(font, ch, offset, color)
    text = (rawbuf[node.start_byte:node.end_byte]
        .decode('utf-8'))
    return minitex.scan_plaintext(text, make_text, node.start_byte)

def scan_plaintext(text, color, offset, font):
    def make_text(ch, offset):
        try:
            ch = texttab[ch]
            return paint_qt5.textbox(font, ch, offset, color)
        except KeyError as _:
            return paint_qt5.textbox(font, ch, offset, color)
    return minitex.scan_plaintext(text, make_text, offset)

#    elements = []
#    offset = 0
#    pas = wp_parser.PState(offset, elements.append)
#    for text in buffer.peek(offset, buffer.length):
#        wp_parser.parse_text(pas, text)
#    wp_parser.parse_done(pas)
#

def scan_text_node(rawbuf, node, color, font):
    text = (rawbuf[node.start_byte:node.end_byte]
        .decode('utf-8'))
    return scan_text(text, color, node.start_byte, font)

def scan_text(text, color, offset, font):
    output = []
    def make_text(ch, offset):
        try:
            ch = texttab[ch]
            return paint_qt5.textbox(font, ch, offset, "#ff0000")
            #return paint_qt5.textbox(font, ch, offset, "#aa88cc")
        except KeyError as _:
            return paint_qt5.textbox(font, ch, offset)
    par_height = font.ascent() + font.descent() + font.leading()
    glue_width = paint_qt5.width_of(font, " ")
    def make_glue(ch, offset):
        nc = ch.count('\n')
        if nc == 1:
            linemark = "/"
            return minitex.hpack([
                minitex.Glue(glue_width/2),
                paint_qt5.textbox(font, linemark, offset+ch.find('\n'), "#b0dcdc"),
                minitex.Glue(glue_width/2) ])
        elif nc > 1:
            return minitex.par(par_height)
        else:
            return minitex.Hint(minitex.Glue(glue_width), 'break', True)
    return minitex.scan_text(text, make_text, make_glue, offset)

#    for element in elements:
#        if isinstance(element, wp_parser.Text):
#            print("lexeme wtf", element)
#            continue
#        if element.rule == 1: # Toplevel text.
#            lexeme = element.contents[0]
#            offset = element.offset + lexeme.offset
#            output.extend(
#                minitex.scan_plaintext(lexeme.text,
#                    make_text, offset))
#        if element.rule == 2: # Toplevel block.
#            attrs = get_attributes(element.contents[0], element.offset)
#            elements = get_elements(element.contents[0], element.offset)
#            output.extend(
#                build_paragraph(elements, attrs, make_text, make_glue,
#                    monofont, font, getfont))
#        if element.rule == 3: # Toplevel attribute.
#            output.append(
#                paint_qt5.textbox(monofont, "(",
#                    element.offset,
#                    "#ff0000"))
#            attr,offs = get_attribute(element.contents[0], element.offset)
#            sp = False
#            for text,offset in zip(attr,offs):
#                if sp:
#                    output.append(
#                        paint_qt5.textbox(monofont, ",", offset-1, "#ff0000"))
#                sp = True
#                output.append(
#                    paint_qt5.textbox(monofont, text, offset, "#0033FF"))
#            output.append(
#                paint_qt5.textbox(monofont, ")",
#                    element.offset+element.length-1,
#                    "#ff0000"))
#        if element.rule == 4: # Toplevel location.
#            pass
#        #print(element.rule)
#
#    #offset = 0
#    #output.extend(
#    #    minitex.scan_plaintext(text, make_text, offset))
#    #offset += len(text)
#    return minitex.vmode(output,
#        minitex.line_break,
#        minitex.align_left,
#        paint_qt5.width_of(font, " "*80))
#    #return paint_qt5.textbox(font, "".join(fulltext), offset)
#    #return elements

def build_paragraph(elements, attrs, make_text, make_glue, monofont, font, getfont):
    output = []
    par_break = minitex.par(font.ascent() + font.descent() + font.leading())
    if ("title",) in attrs:
        font = getfont(32)
        def make_text(ch, offset):
            try:
                ch = texttab[ch]
                return paint_qt5.textbox(font, ch, offset, "#ff0000")
                #return paint_qt5.textbox(font, ch, offset, "#aa88cc")
            except KeyError as _:
                return paint_qt5.textbox(font, ch, offset)
        par_height = font.ascent() + font.descent() + font.leading()
        glue_width = paint_qt5.width_of(font, " ")
        def make_glue(ch, offset):
            nc = ch.count('\n')
            if nc == 1:
                linemark = "/"
                return minitex.hpack([
                    minitex.Glue(glue_width/2),
                    paint_qt5.textbox(font, linemark, offset+ch.find('\n'), "#00ccff"),
                    minitex.Glue(glue_width/2) ])
            elif nc > 1:
                return minitex.par(par_height)
            else:
                return minitex.Hint(minitex.Glue(glue_width), 'break', True)


    for element, offset in elements:
        if element.rule == 1: # Toplevel text.
            lexeme = element.contents[0]
            offset = offset + lexeme.offset
            output.extend(
                minitex.scan_text(lexeme.text, make_text, make_glue, offset))
        if element.rule == 2: # Toplevel block.
            attrs = get_attributes(element.contents[0], offset)
            elements = get_elements(element.contents[0], offset)
            output.extend(
                build_paragraph(elements, attrs, make_text, make_glue,
                    monofont, font, getfont))
        if element.rule == 3: # Toplevel attribute.
            output.append(
                paint_qt5.textbox(monofont, "(",
                    offset,
                    "#ff0000"))
            attr,offs = get_attribute(element.contents[0], offset)
            sp = False
            for text,offs in zip(attr,offs):
                if sp:
                    output.append(
                        paint_qt5.textbox(monofont, ",", offs-1, "#ff0000"))
                sp = True
                output.append(
                    paint_qt5.textbox(monofont, text, offs, "#0033FF"))
            output.append(
                paint_qt5.textbox(monofont, ")",
                    offset+element.length-1,
                    "#ff0000"))
        if element.rule == 4: # Toplevel location.
            pass
    output.append(par_break)
    return output

def get_elements(block, offset):
    elements = []
    while block.rule == 6:
        offset += block.offset
        element = block.contents[0]
        elements.append((element, offset))
        block = block.contents[1]
    assert block.rule == 5
    return elements

def get_attributes(block, offset):
    attrs = []
    while block.rule == 6:
        element = block.contents[0]
        if element.rule == 3:
            attr, _ = get_attribute(element.contents[0],
                element.offset + offset)
            attrs.append(tuple(attr))
        offset += block.offset
        block = block.contents[1]
    assert block.rule == 5
    return attrs

# Routine to extract attribute data.
def get_attribute(attribute, offset):
    if attribute.rule == 7:
        return [""], [attribute.offset+offset]
    elif attribute.rule == 8:
        lexeme = attribute.contents[0]
        offset += attribute.offset + lexeme.offset
        print(lexeme)
        return [lexeme.text], [offset]
    elif attribute.rule == 9:
        offset += attribute.offset
        attr,offs = get_attribute(attribute.contents[0], offset)
        attr.insert(0, "")
        offs.insert(0, offset)
        return attr, offs
    elif attribute.rule == 10:
        offset += attribute.offset
        attr,offs = get_attribute(attribute.contents[1], offset)
        lexeme = attribute.contents[0]
        offset += lexeme.offset
        attr.insert(0, lexeme.text)
        offs.insert(0, offset)
        return attr, offs

LP = chr(0x10)
RP = chr(0x11)
SEP = chr(0x16)

texttab = {
    chr(0x10): '(', # ctrl-P, DLE, 'LP'
    chr(0x11): ')', # ctrl-Q, DC1, 'RP'
    chr(0x12): '[', # ctrl-R, DC2, 'LB'
    chr(0x13): ']', # ctrl-S, DC3, 'RB'
    #chr(0x14): '«', # ctrl-T, DC4, 'AT'
    #chr(0x15): '»', # ctrl-U, NAK, 'TA'
    chr(0x16): ';'} # ctrl-V, SYN, 'SEP'


# def wp_toplevel(elements, env):
#     return minitex.vpack(list(minitex.vbox([
#         wp_layout(element)
#         for element in elements])(env)))
# 
# def wp_layout(element):
#     if isinstance(element, Text):
#         return [element.text]
#     if isinstance(element, Element):
#         result = []
#         for subelement in element.contents:
#             if element.kind in ('blk', 'tab') and isinstance(subelement, Text):
#                 add_par = False
#                 for text in subelement.text.split('\n\n'):
#                     if add_par:
#                         result.append(minitex.par)
#                     result.append(text)
#                     add_par = True
#             else:
#                 result.extend(wp_layout(subelement))
#         is_title = False
#         is_link = False
#         is_table = False
#         is_bold = False
#         for attr in element.attrs:
#             if attr[0] == 'title':
#                 is_title = True
#             if attr[0] == 'ref':
#                 is_link = True
#             if attr[0] == 'table':
#                 is_table = True
#             if attr[0] == 'bold':
#                 is_bold = True
#         if is_table:
#             rows = []
#             for row in element.elements:
#                 rows.append([
#                     wp_layout(elem)
#                     for elem in row.elements])
#             if element.kind in ('blk', 'tab'):
#                 return [minitex.par, minitex.table(rows)]
#             return [minitex.table(rows)]
#         if element.kind in ('blk', 'tab'):
#             if is_title:
#                 def _deco_(env):
#                     env = minitex.let(env,
#                         {'font': env.bigfont,
#                          'font_metrics': env.bigmetrics})
#                     return minitex.fold_all(result, env)
#                 return [minitex.par, _deco_]
#             return [minitex.par] + result
#         if is_link:
#             return [minitex.scope(result, {'is_link': True})]
#         if is_bold:
#             return [minitex.scope(result, {'is_bold': True})]
#         return result
#     return []
