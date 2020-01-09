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



    empty : element → type
    empty e = (e = empty)

    non_empty : element → type
    non_empty e = ∃x.∃y.
        (x:text string|elem element|attr attribute,
         y:element,
         e = cons x y)


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
