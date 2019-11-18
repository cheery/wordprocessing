import wp_parser
import paint_qt5
import minitex

def plaintext_display(buffer, font):
    elements = []
    offset = 0
    pas = wp_parser.PState(offset, elements.append)
    output = []
    def make_text(ch, offset):
        try:
            ch = texttab[ch]
            return paint_qt5.textbox(font, ch, offset, "#aa88cc")
        except KeyError as _:
            return paint_qt5.textbox(font, ch, offset)
    offset = 0
    for text in buffer.peek(offset, buffer.length):
        output.extend(
            minitex.scan_plaintext(text, make_text, offset))
        wp_parser.parse_text(pas, text)
        offset += len(text)
    wp_parser.parse_done(pas)

    return minitex.vmode(output,
        minitex.no_line_break,
        minitex.align_left,
        200)

def full_display(buffer, monofont, font, getfont):
    elements = []
    offset = 0
    pas = wp_parser.PState(offset, elements.append)
    for text in buffer.peek(offset, buffer.length):
        wp_parser.parse_text(pas, text)
    wp_parser.parse_done(pas)

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
                paint_qt5.textbox(font, linemark, offset+ch.find('\n'), "#00ccff"),
                minitex.Glue(glue_width/2) ])
        elif nc > 1:
            return minitex.par(par_height)
        else:
            return minitex.Hint(minitex.Glue(glue_width), 'break', True)

    for element in elements:
        if isinstance(element, wp_parser.Lexeme):
            print("lexeme wtf", element)
            continue
        if element.rule == 1: # Toplevel text.
            lexeme = element.contents[0]
            offset = element.offset + lexeme.offset
            output.extend(
                minitex.scan_plaintext(lexeme.text,
                    make_text, offset))
        if element.rule == 2: # Toplevel block.
            attrs = get_attributes(element.contents[0], element.offset)
            elements = get_elements(element.contents[0], element.offset)
            output.extend(
                build_paragraph(elements, attrs, make_text, make_glue,
                    monofont, font, getfont))
        if element.rule == 3: # Toplevel attribute.
            output.append(
                paint_qt5.textbox(monofont, "(",
                    element.offset,
                    "#ff0000"))
            attr,offs = get_attribute(element.contents[0], element.offset)
            sp = False
            for text,offset in zip(attr,offs):
                if sp:
                    output.append(
                        paint_qt5.textbox(monofont, ",", offset-1, "#ff0000"))
                sp = True
                output.append(
                    paint_qt5.textbox(monofont, text, offset, "#0033FF"))
            output.append(
                paint_qt5.textbox(monofont, ")",
                    element.offset+element.length-1,
                    "#ff0000"))
        if element.rule == 4: # Toplevel location.
            pass
        #print(element.rule)

    #offset = 0
    #output.extend(
    #    minitex.scan_plaintext(text, make_text, offset))
    #offset += len(text)
    return minitex.vmode(output,
        minitex.line_break,
        minitex.align_left,
        paint_qt5.width_of(font, " "*80))
    #return paint_qt5.textbox(font, "".join(fulltext), offset)
    #return elements

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

texttab = {
    chr(0x10): '(', # ctrl-P, DLE, 'LP'
    chr(0x11): ')', # ctrl-Q, DC1, 'RP'
    chr(0x12): '[', # ctrl-R, DC2, 'LB'
    chr(0x13): ']', # ctrl-S, DC3, 'RB'
    chr(0x14): '«', # ctrl-T, DC4, 'AT'
    chr(0x15): '»', # ctrl-U, NAK, 'TA'
    chr(0x16): ','} # ctrl-V, SYN, 'SEP'


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
