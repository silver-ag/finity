from dfa import DFA, IOSymbol, State
from lark import Lark

with open('finity.lark', 'r') as grammar:
    finity_parser = Lark(grammar, start = 'program')
