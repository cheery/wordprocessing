# Wordprocessing file format

If you open a '.wp' file in a text editor,
you will see that it's plain-text with some
control characters interleaved in:

    ^Pdtd^Vdoc^Q
    ^Planguage^Ven^Q
    ^R^Ptitle^Q^Ph1^QSome text^S
    ^RHere's some text^S

The control characters have been carefully selected such that
they're not interfering with any other present-day use of control characters.

If it turns out there are systems that are affected,
the characters may be changed later.
For now the following characters have been renamed:

    hex  ctrl was  wp   presentation
    0x10 ^P   DLE  LP   (
    0x11 ^Q   DCL  RP   )
    0x12 ^R   DC2  LB   [
    0x13 ^S   DC3  RB   ]
    0x16 ^V   SYN  SEP  ;

The wordprocessing format treats everything else as text.

The context free grammar for the format:

    file → element*

    element → TEXT
    element → LB element* RB
    element → LP attribute

    attribute → TEXT? RP
    attribute → TEXT? SEP attribute

The intent of the format is to provide
some rich-text structure into plain-text files.

Due to not needing escape-characters for inserting ordinary characters,
the file format should be easy to edit within an ordinary plaintext editor.

If a plain-text editor is augmented with an incremental parsing library,
such as [treesitter](https://github.com/tree-sitter/tree-sitter),
and graphical layouter/renderer is provided,
then you have the intended editor for this format.

## Type information

To interpret a language,
we'd ideally have a mathematical model
of what stands as a valid element of the format.
The information in context-free-grammar can be duplicated in a type:

    file, element, attribute, text : type

    file      = element
    element   = list (text string | elem element | attr attribute)
    attribute = (string, list string)

But now we're able to specify more things.

The element is canonical if every sub-element in it is canonical,
and the following transformation does not change the element:

    canon_fn : element → element
    canon_fn = foldr compact []

    compact : node -> element -> element
    compact (text s) (cons (text v) z) = cons (text (s ++ v)) z
    compact a        z                 = cons a z

We could state the property as such:

    is_canonical : element → type
    is_canonical elem = (canon_fn elem = elem)

We specify that every element has a shape.

    shape : element → set signature
    shape (empty) = empty
    shape (cons (text _) rest) = shape rest
    shape (cons (elem _) rest) = shape rest
    shape (cons (attr a) rest) = shape rest | singleton (signature_of a)

The shape is a set of signatures collected from the attributes of the element.
Signature is the first field in the attribute paired with it's arity.

    signature : type
    signature = (string, nat)

    signature_of : attribute → signature
    signature_of = (first, rest) = (first, length rest + 1)

For clarity I've provided some type information for
the lists and primitive structures used in the specification.

    list : type → type
    list a = ind (list ↦ empty | cons a list)

    nat : type
    nat = ind (nat ↦ zero 1 | succ nat)

    string : type
    string = ind (string ↦ empty | cons nat string)

    fromInt   :     nat → string
    length    : ∀a. list a → nat 
    singleton : ∀a. a → set a
    (|)       : ∀a. set a → set a → set a
    (+)       :     nat → nat → nat
    (++)      :     string → string → string

Though I expect that these are provided.

## Notions of further validity

Valid markup is rarely what we want,
as usually we are looking for well-formed structures
that represent some subject of interest.

To get useful notions of validity,
we rely on type information again.
Notions of what stands as a valid element are provided
by types indexed with elements.

    a_valid_element : type
    a_valid_element = ∃e. (e : element), valid e

    valid : element → type

This allows type-theoretic build-up of validators.
For example here's a structure that can be only constructed
if the element is empty, and respectively for ensuring the element is non-empty.

    empty : element → type
    empty e = (e = empty)

    non_empty : element → type
    non_empty e = ∃x.∃y.
        (x:text string|elem element|attr attribute,
         y:element,
         e = cons x y)

We can give this a deeper treatment later.
For now lets look at one use-case
that is document generation through pandoc.

## Pandoc -usecase

Pandoc is an universal markup converter
that gives a good juicy platform.
If translation of wordprocessing files to Pandoc succeed well,
then the files can be exported to a large variety of document formats.

Pandoc consist of a Meta -field & list of blocks.

    data Pandoc = Pandoc Meta [Block]

    newtype Meta = Meta { unMeta :: M.Map Text MetaValue }

Meta values is something like your JSON + some structure.

    data MetaValue = MetaMap (M.Map Text MetaValue)
                   | MetaList [MetaValue]
                   | MetaBool Bool
                   | MetaString Text
                   | MetaInlines [Inline]
                   | MetaBlocks [Block]

Blocks seem to represent vertically layouted elements.

    data Block
        = Plain [Inline]        -- ^ Plain text, not a paragraph
        | Para [Inline]         -- ^ Paragraph
        | LineBlock [[Inline]]  -- ^ Multiple non-breaking lines
        | CodeBlock Attr Text -- ^ Code block (literal) with attributes
        | RawBlock Format Text -- ^ Raw block
        | BlockQuote [Block]    -- ^ Block quote (list of blocks)
        | OrderedList ListAttributes [[Block]] -- ^ Ordered list (attributes
                                -- and a list of items, each a list of blocks)
        | BulletList [[Block]]  -- ^ Bullet list (list of items, each
                                -- a list of blocks)
        | DefinitionList [([Inline],[[Block]])]  -- ^ Definition list
                                -- Each list item is a pair consisting of a
                                -- term (a list of inlines) and one or more
                                -- definitions (each a list of blocks)
        | Header Int Attr [Inline] -- ^ Header - level (integer) and text (inlines)
        | HorizontalRule        -- ^ Horizontal rule
        | Table [Inline] [Alignment] [Double] [TableCell] [[TableCell]]  -- ^ Table,
                                -- with caption, column alignments (required),
                                -- relative column widths (0 = default),
                                -- column headers (each a list of blocks), and
                                -- rows (each a list of lists of blocks)
        | Div Attr [Block]      -- ^ Generic block container with attributes
        | Null                  -- ^ Nothing

Inline elements seem to be 'groups', insertions, or pieces within text.

    data Inline
        = Str Text            -- ^ Text (string)
        | Emph [Inline]         -- ^ Emphasized text (list of inlines)
        | Strong [Inline]       -- ^ Strongly emphasized text (list of inlines)
        | Strikeout [Inline]    -- ^ Strikeout text (list of inlines)
        | Superscript [Inline]  -- ^ Superscripted text (list of inlines)
        | Subscript [Inline]    -- ^ Subscripted text (list of inlines)
        | SmallCaps [Inline]    -- ^ Small caps text (list of inlines)
        | Quoted QuoteType [Inline] -- ^ Quoted text (list of inlines)
        | Cite [Citation]  [Inline] -- ^ Citation (list of inlines)
        | Code Attr Text      -- ^ Inline code (literal)
        | Space                 -- ^ Inter-word space
        | SoftBreak             -- ^ Soft line break
        | LineBreak             -- ^ Hard line break
        | Math MathType Text  -- ^ TeX math (literal)
        | RawInline Format Text -- ^ Raw inline
        | Link Attr [Inline] Target  -- ^ Hyperlink: alt text (list of inlines), target
        | Image Attr [Inline] Target -- ^ Image:  alt text (list of inlines), target
        | Note [Block]          -- ^ Footnote or endnote
        | Span Attr [Inline]    -- ^ Generic inline container with attributes

There are smaller elements within this structure, but you probably get the idea.
It's a complex intermediate structure that needs to cover many contexts
while somewhat capture the things that people care about in documents.

The procedure to produce looks following:

    readWordProcessing :: PandocMonad m
                       => ReaderOptions -- ^ Reader options
                       -> Text          -- ^ String to parse (assuming @'\n'@ line endings)
                       -> m Pandoc

To start this off we better build a function that just parses WP into elements.

    parseWP :: Text -> Either ParseError Element

There's such a parser in the `haskell-parser/Main.hs`.

I'm in middle of implementing [the WordProcessing-format][pd] into pandoc.

 [pd]: https://github.com/cheery/pandoc

### Pandoc document data type

The document data type must be declared in the beginning of the document.

    (dtd;pandoc)

This is the only element that must be positioned topmost for now.

The remaining contents of the pandoc document are scanned through.
The `meta/3` attributes are interpreted as meta-fields.
For example you can identify the language of the document like this:

    (meta;lang;en)

The identification of block/inlines are looked up from the shape of the element,
except that the shape includes only the attributes
that appear exactly once within an element.

Otherwise inside a toplevel-element, if there is an unique `meta/2` -attribute,
it'll be used up as an attribute.

### Pandoc meta attributes

If the element is a meta-element, the shape of the element is analysed.

If there's `(^)` -attribute in the field,
the whole element is interpreted as a block.

These should be self-explanatory:

    (map) [(key;_)value] [(key;_)value] [(key;_)value]
    (list) [_] [_] [_] [_]
    (true)
    (false)
    (string)text

If there are no attributes other than the meta,
the field is interpreted as an inline field.

### Paragraph block breaking

For presentation or translation purposes it may be preferable
to break a paragraph block into smaller elements.
The type for such function would be:

    break_paragraph : element → list element

To implement it,
bring the element into a canonical form if it already is not.
Now for every text block in the element list,
find longest non-overlapping sequences
matching the following regular expression:

    \n[ \t\r\n]*\n

Split the text, replacing the sequences with paragraph splitting markers,
then split the whole element from those markers into smaller elements.

## Processing rules

The file is considered to be plaintext structure
consisting of attributes, text and elements.
During the normal use the topmost plaintext is treated as a comment layer.

Each attribute is identified
by their first field and the amount of fields.
For example: `(dtd;doc)` is identified as `dtd/2`

The file describes one or more dtds
and dtds describe how the file is interpreted.

Each attribute is interpreted by the context where it appears,
for example here's all the elements detected by the `doc` -DTD:

    dtd;doc

        context            id         description
        file Ø             par        paragraph block
        file title/1       title      title text
        file h1/1          h1         heading
        file h2/1          h2         sub-heading
        file h3/1          h3         sub-sub-heading
        file h4/1          h4         sub-sub-sub-heading
        file img/2         img        image
        file par Ø         span       text span      
        (par|span) img/2   inl-img    inline image
        (par|span) href/2  hypertext  link

The `Ø` means that there are no other ways to identify the element present.
Other than that, I haven't entirely decided how the context is marked yet.

Some use-cases should be presented and evaluated
before deciding how the elements are identified in a file.

## Paragraph blocks

The paragraph blocks are areas where text is interpreted as a paragraph.
Inside these blocks an empty line sets a new paragraph.
Any attributes inside this block still affect the whole block.

Some people may eventually be frustrated
that the whole file is not a single paragraph block.

The rationale for this choice is that without separate
marking of paragraph blocks,
there would be multiple ways to interpret where a paragraph ends
before some other element is presented.

Also, the topmost layer is not wasted.
When it's not used for anything else,
it can be used for writing comments or notes relevant to
people working on the document.

Programming languages may use the topmost layer,
providing literate text files or procedural documents.

## Contents of this directory

 * `wp_pyqt5/` contains an experimental Python3/Qt5 text editor.
   The intent of this project is to explore the implementation
   and indentify potential issues that affect the implementation.
   It's not a reference implementation though.
   Any specification is put into specification documents or into this README.
 * `grammar.txt` contains the grammar,
   though it's described in the README already.
 * `wp.vim` contains some macros to operate the files in Vim.
   Though I really would want the incremental parsing utilities into Vim.

## State of the project

The project is in a "dogfooding" -phase.
I'm beginning to put the format into an use
and see how it works in practice.

The pandoc-support for the format:
Dumps out the whole input file as paragraphs.
Error handling absent in parser.
