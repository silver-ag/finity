import math

MAXINT = 4

# DATASTRUCTURE
# an FSM is a set of states. each state has a name, one output (a string) and zero (halt), one (epsilon) or many (input) transitions.

class State:
    def __init__(self, name, variables = None):
        self.name = name
        if variables is not None:
            self.variables = {k:v for k,v in variables.items()} # need a copy
        else:
            self.variables = variables
        self.hash_cache = hash(repr(self))
    def __eq__(self, other):
        return isinstance(other, State) and self.hash_cache == other.hash_cache
        #return isinstance(other, State) and self.name == other.name and set(self.variables) == set(other.variables) and all([self.variables[k] == other.variables[k] for k in self.variables])
    def __hash__(self):
        return self.hash_cache
    def __repr__(self):
        if self.variables is not None:
            return f"<{self.name}: {self.variables}>"
        else:
            return f"<{self.name}>"

class FSM:
    def __init__(self, states):
        self.states = states # {'state1name': ('outputstring', (None | 'nextstatename' | {0: 'nextstatename', ...})), ...}
    def run(self, start_state=State('start')):
        state = start_state
        while True:
            output, transition = self.states[state]
            if output is not None:
                print(output, end='')
            if transition is None: # halt
                return True
            elif isinstance(transition, State): # epsilon
                state = transition
            elif isinstance(transition, dict): # input
                try:
                    number_in = int(input())
                except:
                    print(f"\nRuntime Error: input must be an integer\n")
                    return False
                if number_in < 0 or number_in > MAXINT-1:
                    print(f"\nRuntime Error: input must be 0-{MAXINT-1}\n")
                    return False
                if number_in in transition:
                    state = transition[number_in]
                else:
                    return True #  halt

# OPTIMISER

def optimise(fsm, verbose=True):
    if verbose:
        print('optimising, number of partitions: 1')
    partition = [list(fsm.states.keys())]
    partition_locations = {}
    for k in fsm.states.keys():
        if fsm.states[k][1] is None:
            partition_locations[k] = None
        elif isinstance(fsm.states[k][1], State):
            partition_locations[k] = 0
        else: # input
            partition_locations[k] = {i:0 for i in range(MAXINT)}
    while True:
        if verbose:
            print(len(partition))
        new_partition = []
        new_partition_locations = {}
        top_eqc_pointer = 0
        for eqc in partition:
            subpartition = [[eqc[0]]]
            new_partition_locations[eqc[0]] = top_eqc_pointer
            for state in eqc[1:]:
                lonely = True
                for i in range(len(subpartition)):
                    if indistinguishable(subpartition[i][0], state, partition_locations, fsm.states):
                        subpartition[i].append(state)
                        new_partition_locations[state] = i + top_eqc_pointer
                        lonely = False
                        break
                if lonely:
                    subpartition.append([state])
                    new_partition_locations[state] = i + top_eqc_pointer + 1
            new_partition.append(subpartition)
            top_eqc_pointer += len(subpartition)
        new_partition = sum(new_partition, [])
        if partition == new_partition:
            break
        else:
            partition = new_partition
            partition_locations = new_partition_locations
    if verbose:
        print(f'minimised to {len(partition)} states')
    optimised_version = {}
    for i in range(len(partition)):
        transition = fsm.states[partition[i][0]]
        if State('start') in partition[i]:
            i = 'start'
        if transition[1] is None:
            optimised_version[State(i)] = list(transition)
        elif isinstance(transition[1], State):
            optimised_version[State(i)] = [transition[0], State(partition_locations[transition[1]])]
        else:
            transition_map = {}
            for n in range(MAXINT):
                transition_map[n] = State(partition_locations[transition[1][n]])
            optimised_version[State(i)] = [transition[0], transition_map]
    # strip blank epsilons
    while True:
        if verbose:
            print(len(optimised_version))
        made_change = False
        for state in list(optimised_version.keys()):
            if (state in optimised_version and
                isinstance(optimised_version[state][1], State) and
                optimised_version[state][0] is None and
                optimised_version[state][1] != state):
                
                made_change = True
                target = optimised_version[state][1]
                target_transition = optimised_version[target]
                #if target == State('start'): # keep the name start
                #    target = state
                #    state = State('start')
                optimised_version.pop(target)
                optimised_version[state] = target_transition
                for other_state in optimised_version:
                    if optimised_version[other_state][1] == target:
                        optimised_version[other_state][1] = state
                    elif isinstance(optimised_version[other_state][1], dict):
                        for i in range(MAXINT):
                            if optimised_version[other_state][1][i] == target:
                                optimised_version[other_state][1][i] = state
        if not made_change:
            break
    if verbose:
        print(f'stripped blank epsilons to {len(optimised_version)} states')
        print('optimised\n')

    return FSM(optimised_version)

def indistinguishable(state_a, state_b, partition_locations, states):
    transition_a = states[state_a]
    transition_b = states[state_b]
    if transition_a[0] != transition_b[0]:
        return False
    if transition_a[1] is None:
        return transition_b[1] is None
    if isinstance(transition_a[1], State) and isinstance(transition_b[1], State):
        return partition_locations[transition_a[1]] == partition_locations[transition_b[1]]
    if isinstance(transition_a[1], dict) and isinstance(transition_b[1], dict):
        same = True
        for i in range(MAXINT):
            if partition_locations[transition_a[1][i]] != partition_locations[transition_b[1][i]]:
                same = False
        return same
    return False
        

#LANGUAGE
    
# so:
# a langauge whose only flow control is gotos and conditional gotos
# a function that runs through it cataloging output and variable values,
# and when it reaches an input it recurses with 'here are the states we've reached so far, keep going' for every possibility

from lark import Lark, Transformer
from ast import literal_eval

with open('finitygrammar.lark') as grammar:
    parser = Lark(grammar.read(), start='program')

def parse(filename):
    with open(filename) as file:
        AST = parser.parse(file.read())
    label_index = {}
    for i in range(len(AST.children)):
        line = AST.children[i]
        if line.data == "label":
            label_index[line.children[0].value] = i
    return (AST, label_index)

def generate_states_with_progress(AST, label_index):
    max_total_states = len(AST.children) * (MAXINT ** len(set([line.children[0].value for line in AST.children if line.data in ('input', 'assignment')])))
    print(f'loose upper bound on maximum number of states that might be generated: {max_total_states}')
    states = generate_states(AST, label_index, maximum_number = max_total_states)
    print(f'generated a total of {len(states)} states')
    return states

def generate_states(AST, label_index, line_pointer = 0, variables = None, states = None, maximum_number = None):
    if variables is None:
        variables = {}
    if states is None:
        states = {}
    while True:
        variables = {k:v for k,v in variables.items()}
        this_state = State(line_pointer, variables)
        if line_pointer >= len(AST.children):
            states[this_state] = (None, None)
            return states
        if this_state in states:
            return states # found loop
        line = AST.children[line_pointer]
        if line.data == 'goto':
            line_pointer = label_index[line.children[0]]
            states[this_state] = (None, State(line_pointer, variables))
        elif line.data == 'conditionalgoto':
            if run_expression(line.children[1], variables):
                line_pointer = label_index[line.children[0]]
            else:
                line_pointer += 1
            states[this_state] = (None, State(line_pointer, variables))
        elif line.data == 'input':
            states[this_state] = (None, {i: State(line_pointer + 1, variables | {line.children[0].value: i}) for i in range(MAXINT)})
            for n in range(MAXINT):
                states = generate_states(AST, label_index, line_pointer + 1, {k:v for k,v in variables.items()} | {line.children[0].value: n}, states, maximum_number)
            return states
        elif line.data == 'output':
            line_pointer += 1
            if line.children[0].type == 'STRING':
                states[this_state] = (literal_eval(line.children[0].value), State(line_pointer, variables))
            elif line.children[0].type == 'VARNAME':
                states[this_state] = (variables[line.children[0].value], State(line_pointer, variables))
            else:
                print(f'unknown type to output: {line.children[0].type}')
                exit()
        elif line.data == 'assignment':
            variables[line.children[0].value] = run_expression(line.children[1], variables)
            line_pointer += 1
            states[this_state] = (None, State(line_pointer, variables))
        elif line.data == 'label':
            line_pointer += 1
            states[this_state] = (None, State(line_pointer, variables))
        else:
            print(f'unknown command: {line.data}')
            line_pointer += 1
            states[this_state] = (None, State(line_pointer, variables))
        if maximum_number is not None and maximum_number >= 100 and len(states) % (maximum_number//100) == 0:
            print(f'{round(100*len(states)/maximum_number)}%')
        

def run_expression(expr, variables):
    kind = expr.children[0].data
    if kind == 'value':
        if expr.children[0].children[0].type == 'VARNAME':
            return variables[expr.children[0].children[0].value]
        elif expr.children[0].children[0].type == 'NUMBER':
            return int(expr.children[0].children[0].value)
    elif kind == 'operation':
        a = run_expression(expr.children[0].children[0], variables)
        b = run_expression(expr.children[0].children[2], variables)
        op = expr.children[0].children[1]
        if op == '+':
            return a + b
        elif op == '-':
            return a - b
        elif op == '*':
            return a * b
        elif op == '/':
            return '//'
        elif op == '>':
            return 1 if a > b else 0
        elif op == '<':
            return 1 if a < b else 0
        elif op == '==':
            return 1 if a == b else 0
        else:
            print(f'unrecognised op {op}')
    elif kind == 'expression': # in brackets
        return run_expression(expr.children[0], variables)


def compile(filename, verbose=True):
    if verbose:
        states = generate_states_with_progress(*parse(filename))
        print('compiled\n')
    else:
        states = generate_states(*parse(filename))
    states[State('start')] = states[State(0,{})]
    states.pop(State(0,{}))
    return FSM(states)
