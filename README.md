# FINITY

finity is a language that compiles to a finite automaton. it achieves this by requiring a recursion depth cap and an explicit finite valid set of values for each variable, each of which has defaults but can be set explicitly. it takes advantage of the computational tractability of finite automata to allow the programmer to specify conditions like 'if function f halts on argument a'
