import os
from tree_sitter import Language, Parser

dname = os.path.dirname(__file__)
so_path = os.path.join(dname, "./tree-sitter-wp.so")

Language.build_library(so_path, [
    os.path.join(dname, 'tree-sitter-wordprocessing')])

WP_LANGUAGE = Language(so_path, 'wordprocessing')

parser = Parser()
parser.set_language(WP_LANGUAGE)
