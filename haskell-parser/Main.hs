module Main where

import Data.Text (Text, pack, groupBy, head)
import Data.Text.IO (readFile, putStrLn)
import System.Environment (getArgs)
import Data.List (intercalate)
import System.Exit (exitWith, ExitCode(..))
import System.IO (stderr, hPutStrLn)

main = do
    args <- getArgs
    case length args of
        0 -> exitWithError "Too few arguments" 1
        1 -> return ()
        _ -> exitWithError "Too many arguments" 1
    let pathname = (args !! 0)
    input <- Data.Text.IO.readFile pathname 

    Prelude.putStrLn (show (parseWP input))
    --let root = [Text (pack "foo")]
    --Prelude.putStrLn (show root)

exitWithError str n = do
    System.IO.hPutStrLn stderr ("error: " ++ str)
    exitWith (ExitFailure n)


-- This is a generated LR0 grammar
-- python parsergen4.py ../wordprocessing/grammar.txt
--        -p -o ../wordprocessing/wp_parser2_tables.py --lr0
symtab :: [String]
symtab = ["LB", "LP", "RB", "RP", "SEP", "TEXT", "element", "block", "attribute"]

rtab :: [(Int, [Bool])]
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

state :: [[Int]]
state = [ [1, 2, 0, 0, 0, -2, -1, 0, 0],
          [1, 2, -5, 0, 0, -2, 3, -3, 0],
          [0, 0, 0, -7, 5, 4, 0, 0, -4],
          [1, 2, -5, 0, 0, -2, 3, -6, 0],
          [0, 0, 0, -8, 6, 0, 0, 0, 0],
          [0, 0, 0, -7, 5, 4, 0, 0, -9],
          [0, 0, 0, -7, 5, 4, 0, 0, -10]]

-- Control character table
ctrtab :: Char -> Int
ctrtab '\x10' = 1 -- ctrl-P, DLE, 'LP'
ctrtab '\x11' = 3 -- ctrl-Q, DC1, 'RP'
ctrtab '\x12' = 0 -- ctrl-R, DC2, 'LB'
ctrtab '\x13' = 2 -- ctrl-S, DC3, 'RB'
ctrtab '\x16' = 4 -- ctrl-V, SYN, 'SEP'
ctrtab _    = 5   -- 'TEXT'

-- Output from the parser
type Element = [Node]
type ParseError = ()

data Node = Text Text | Elem Element | Attr Text [Text]
    deriving (Show)

-- Tokenizing faces no error conditions.
tokenize :: Text -> [(Int, Text)]
tokenize = map nameIt . groupText
    where
    nameIt x = (ctrtab (Data.Text.head x), x)

groupText = groupBy rule
    where
    rule x y = (ctrtab x == 5) && (ctrtab y == 5)

-- The parsing routine 
data Stack = Initial | Cell Stack Int Node
data Parse = Failure | OK [Node] Stack

parseWP :: Text -> Either ParseError Element
parseWP text = finish (foldr f (\x -> x) (tokenize text) (OK [] Initial))
    where
    f (g,txt) remaining = remaining . scan (g, Text txt)

scan :: (Int, Node) -> Parse -> Parse
scan a Failure = Failure
scan (g,x) (OK elem s) =
    case get_action s g of
        Shift k -> (OK elem (Cell s k x))
        Reduce n -> let
            (g',r) = rtab !! n
            (s',z) = peel x s r
            in if n == 0
                then (OK (reverse z ++ elem) s')
                else scan (g',interp n (reverse z)) (OK elem s')
        Error -> Failure

finish :: Parse -> Either ParseError Element
finish Failure = Left ()
finish (OK elem Initial) = Right (reverse elem)
finish (OK elem _) = Left ()

peel :: Node -> Stack -> [Bool] -> (Stack, [Node])
peel n a [True] = (a, [n])
peel n a [False] = (a, [])
peel n (Cell p _ m) (True:q) = let (p',ns) = peel m p q in (p', n:ns)
peel n (Cell p _ m) (False:q) = let (p',ns) = peel m p q in (p', ns)

get_action :: Stack -> Int -> Action
get_action s g =
    let k = get_state s
        a = (state !! k) !! g
    in if a < 0
        then Reduce (-1 - a)
        else if a == 0
            then Error
            else Shift a

get_state (Initial)    = 0
get_state (Cell p k n) = k

data Action = Shift Int | Reduce Int | Error

interp :: Int -> [Node] -> Node
interp 0 [a] = a
interp 1 [text] = text
interp 2 [block] = block
interp 3 [attr] = attr
interp 4 [] = Elem []
interp 5 [item, Elem block] = Elem (item : block)
interp 6 [] = Attr (pack "") []
interp 7 [Text a] = Attr a []
interp 8 [Attr b blk] = Attr (pack "") (b:blk)
interp 9 [Text a, Attr b blk] = Attr a (b:blk)
interp a b = (error (show (a,b)))

