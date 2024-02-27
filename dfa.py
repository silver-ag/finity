
# the specific way we define a DFA is:
#  there is a collection of states, each of which has a transition table
#  the transition set can be either an epsilon transition or a set of input transitions
#   if it's an epsilon transition it happens unconditionally
#   if its a set of input transitions then an input symbol is read and the appropriate transition occurs if applicable, otherwise the machine halts where it is
#   if there's no input symbol available, then a special IOSymbol('eof') is read
# output is associated with transitions and is produced when they're followed

"""
tools for deterministic finite automata

the automata defined here are able to produce output as well as take input. for mathematical purposes this is equivalent to an
ordinary finite automaton that takes a language like "in(symbols)out(symbols)in(symbols)out(symbols)..."

exports:
IOSymbol\t- a class of symbol suitable for the alphabet
State\t- a class for automaton states, which store their transitions
Transition\t- a class for unconditional transitions, which includes their output
TransitionsRow\t - a class for a transition table row, mapping input IOSymbols to Transitions
DFA\t - a class for the DFA itself
"""

from itertools import combinations

class IOSymbol:
    """a class of symbol equipped with types, to permit clarity with symbols like <EOF>"""
    kinds = ['char', 'eof']
    def __init__(self, kind, value = None):
        """takes a type from IOSymbol.kinds and an optional arbitrary value"""
        if kind not  in self.kinds:
            raise Exception(f"unrecognised IOSymbol kind: {kind}")
        self.kind = kind
        self.value = value
    def __eq__(self, other):
        return isinstance(other, IOSymbol) and self.kind == other.kind and self.value == other.value
    def __hash__(self):
        return hash(self.kind + str(self.value))
    def __str__(self):
        if self.kind == 'char':
            return self.value
        elif self.kinf == 'eof':
            return '<EOF>'
        else:
            return repr(self)
    def __repr__(self):
        return f"<IOSymbol '{self.value}' ({self.kind})>"

class State:
    """a class for DFA states, storing a name and the transitions that leave this state"""
    def __init__(self, name, transitions = None):
        """takes a name and an optional transitions argumant that may be an unconditional Transition, a TransitionRow, or a string or dict that will be used to construct one of those two repsectively"""
        self.name = name
        if isinstance(transitions, str):
            self.transitions = Transition(transitions)
        elif isinstance(transitions, dict):
            self.transitions = TransitionsRow(transitions)
        elif isinstance(transitions, Transition) or isinstance(transitions, TransitionsRow):
            self.transitions = transitions
    def __eq__(self, other):
        if isinstance(other, State) and self.name == other.name:
            if self.transitions != other.transitions:
                raise(f"shouldn't happen - two states with the same name but different transitions ({self.transitions}, {self.output} or {other.transitions})")
            else:
                return True
        return False
    def __hash__(self):
        return hash(self.name)
    def __str__(self):
        return self.name
    def __repr__(self):
        return f"<State: {str(self)}>"

class Transition:
    """a small class for a transition, storing a destination state name and an optional output list of IOSymbols"""
    def __init__(self, state_to, output = []):
        """takes a destination state name and an optional output list of IOSymbols"""
        self.state_to = state_to
        self.output = output if isinstance(output, list) else [output]

class TransitionsRow:
    """a class for a row on the transition table"""
    def __init__(self, inputs):
        """takes input in the form {<IOSymbol input>: <Transition>, ...}"""
        self.inputs = inputs

class DFA:
    """a class for a finite automaton

    provides decide and minimise functions as well as the ability to run the automaton directly."""
    def __init__(self, start, states, minimise = True):
        """takes a starting state name and a list of States. minimises automatically by default, this can be disabled with the minimise argument"""
        self.states = {}
        for state in states:
            if state.name in self.states:
                raise Exception(f"DFA given duplicate state name: {state}, {self.states[state.name]}")
            else:
                self.states[state.name] = state
        self.start = start
        if start not in self.states:
            print(self.states)
            raise Exception(f"DFA given nonexistant start state '{start}'")
        
        self.epsilons_minimised = False
        if minimise:
            self.minimise()
    def minimise_epsilons(self):
        """remove all epsilon transitions except those that point back at the state they come from"""
        while True:
            removed = False
            for state in self.states.values():
                if isinstance(state.transitions, Transition):
                    for other_state in self.states.values():
                        if isinstance(other_state.transitions, Transition):
                            if other_state.transitions.state_to == state.name:
                                other_state.transitions.state_to = state.transitions.state_to
                                other_state.transitions.output += state.transitions.output
                        elif isinstance(other_state.transitions, TransitionsRow):
                            for symbol in other_state.transitions.inputs:
                                if other_state.transitions.inputs[symbol].state_to == state.name:
                                    other_state.transitions.inputs[symbol].state_to = state.transitions.state_to
                                    other_state.transitions.inputs[symbol].output += state.transitions.output
                    removed = state.name
                    break
            if removed:
                self.states.pop(removed)
            else:
                break
        self.epsilons_minimised = True
    def run(self, start = None, input_buffer = []):
        """run the automaton, starting from the default start state unless otherwise specified, on the given input list of IOSymbols"""
        if start is None:
            start = self.start
        current_state = self.states[start]
        while True:
            next_state, output, input_buffer = self.step(current_state, input_buffer)
            if len(output) > 0:
                print([str(sym) for sym in output])
            if next_state is None:
                print(f"HALT at {current_state}")
                return True
            else:
                current_state = next_state
    def step(self, state, input_buffer):
        """make one transition from the given state using the given input list of IOSymbols.

        returns (<next State>, <output list of IOSymbols>, <remaining input list of IOSymbols>)"""
        if state.transitions is None:
            next_state_name = None
            output = []
        elif isinstance(state.transitions, Transition):
            next_state_name = state.transitions.state_to
            output = state.transitions.output
        elif isinstance(state.transitions, TransitionsRow):
            if len(input_buffer) > 0:
                input_symbol = input_buffer[0]
                input_buffer = input_buffer[1:]
            else:
                input_symbol = IOSymbol('eof')
            if input_symbol in state.transitions.inputs:
                next_state_name = state.transitions.inputs[input_symbol].state_to
                output = state.transitions.inputs[input_symbol].output
            else:
                next_state_name = None
                output = []
        
        if next_state_name is None:
            next_state = None
        elif next_state_name not in self.states:
            raise Exception(f"transition to nonexistant state '{new_state_name}' from '{state}'")
        else:
            next_state = self.states[next_state_name]
        return (next_state, output, input_buffer)
    def decide(self, start, possible_inputs):
        """decide whether the DFA will or may halt, starting from state <start> with allowed input alphabet <possible_inputs>"""
        def decide_recursive(start, visited = []) :
            if start in visited:
                return (False, True)
            elif self.states[start].transitions is None:
                return (True, False)
            elif isinstance(self.states[start].transitions, Transition):
                return decide_recursive(self.states[start].transitions.state_to, visited + [start])
            elif isinstance(self.states[start].transitions, TransitionsRow):
                options = []
                possible_input_values = 0
                for input_value in self.states[start].transitions.inputs:
                    if input_value in possible_inputs:
                        options.append(decide_recursive(self.states[start].transitions.inputs[input_value].state_to, visited + [start]))
                        possible_input_values += 1
                if possible_input_values < len(possible_inputs):
                    options.append((True,False))
                result = (False, False)
                for i in range(len(options)):
                    result = (options[i][0] or result[0], options[i][1] or result[1])
                return result
        halt_possible, loop_possible = decide_recursive(start)
        if halt_possible and loop_possible:
            return 'may run forever or halt depending on input'
        elif (not halt_possible) and loop_possible:
            return 'will run forever regardless of input'
        elif halt_possible and (not loop_possible):
            return 'will halt eventually regardless of input'
        else:
            raise Exception(f"should not happen: apparently neither loops nor halts")
    def minimise(self):
        """minimise DFA

        ensures that if the default start state is indistinguishable from some others, the resulting aggregate state has the name of the start state rather than any of the others"""
        if not self.epsilons_minimised:
            self.minimise_epsilons()
        distinctness_table = {pair: None for pair in combinations(self.states.keys(), 2)}
        def distinguish(state_a, state_b, visited):
            state_a = self.states[state_a]
            state_b = self.states[state_b]
            #print(f"{state_a} {state_b} {visited}")
            if state_a == state_b:
                #print(f"0 {state_a} {state_b} False")
                return False # no need to record distinctness of a state from itself
            if state_a.name in visited:
                #print(f"1 {state_a} {state_b} {state_b not in visited[state_a]}")
                return record_distinctness(state_a, state_b, state_b.name not in visited[state_a.name])
            if state_a.transitions is None:
                #print(f"2 {state_a} {state_b} {state_b.transitions is not None}")
                return record_distinctness(state_a, state_b, state_b.transitions is not None)
            if isinstance(state_a.transitions, Transition) and isinstance(state_b.transitions, Transition):
                if state_a.transitions.output == state_b.transitions.output:
                    assert(state_a.transitions.state_to == state_a.name and state_b.transitions.state_to == state_b.name, "uneliminated non-looping epsilon transition found")
                    #print(f"3 {state_a} {state_b} False")
                    return record_distinctness(state_a, state_b, False)
            if isinstance(state_a.transitions, TransitionsRow) and isinstance(state_b.transitions, TransitionsRow):
                if set(state_a.transitions.inputs.keys()) != set(state_b.transitions.inputs.keys()):
                    #print(f"4 {state_a} {state_b} True")
                    return record_distinctness(state_a, state_b, True)
                if state_a.name in visited:
                    visited[state_a.name].add(state_b.name)
                else:
                    visited[state_a.name] = set([state_b.name])
                transitions_a = state_a.transitions.inputs
                transitions_b = state_b.transitions.inputs
                r = any([transitions_a[symbol].output == transitions_b[symbol].output
                         and distinguish(transitions_a[symbol].state_to, transitions_b[symbol].state_to, dict(visited))
                         for symbol in state_a.transitions.inputs])
                #print(f"5 {state_a} {state_b} {r}")
                return record_distinctness(state_a, state_b, r)
            #print(f"6 {state_a} {state_b} True")
            return record_distinctness(state_a, state_b, True)
        def record_distinctness(state_a, state_b, v):
            if (state_a.name, state_b.name) in distinctness_table:
                distinctness_table[(state_a.name, state_b.name)] = v
                return v
            elif (state_b.name, state_a.name) in distinctness_table:
                distinctness_table[(state_b.name, state_a.name)] = v
                return v
            else:
                raise Exception(f"state pair not found in distinctness table: {state_a}:{type(state_a)}, {state_b}:{type(state_b)}")
        n = 0
        for pair in distinctness_table:
            if distinctness_table[pair] is None:
                n += 1
                distinguish(pair[0], pair[1], {})
        print(f"{n}/{len(distinctness_table)}")
        #print(distinctness_table)
        # use table to sort into equivalence classes each with a representative member
        equivalence_classes = {list(self.states.keys())[n]: n for n in range(len(self.states))}
        for pair in distinctness_table:
            if not distinctness_table[pair]:
                equivalence_classes[pair[0]] = equivalence_classes[pair[1]]
        representative_states = {}
        for state in self.states:
            # make sure self.start is the representative of its class
            if (equivalence_classes[state] not in representative_states) or representative_states[equivalence_classes[state]] != self.start:
                representative_states[equivalence_classes[state]] = state
        # actually do the minimisation
        to_remove = []
        for state in self.states.values():
            if state.name not in representative_states.values():
                to_remove.append(state.name)
            else:
                if isinstance(state.transitions, Transition):
                    state.transitions.state_to = representative_states[equivalence_classes[state.transitions.state_to]]
                elif isinstance(state.transitions, TransitionsRow):
                    for symbol in state.transitions.inputs:
                        state.transitions.inputs[symbol].state_to = representative_states[equivalence_classes[state.transitions.inputs[symbol].state_to]]
        for state in to_remove:
            self.states.pop(state)

test = DFA('A',
           [State('A', transitions = {IOSymbol('char','a'): Transition('B1', [IOSymbol('char','x')]), IOSymbol('char','b'): Transition('preB2', [])}),
            State('preB2', transitions = Transition('B2', [IOSymbol('char','y')])), # eliminated by epsilon minimisiation
            State('B1', transitions = {IOSymbol('char','c'): Transition('A', output = [IOSymbol('char','z')])}),
            State('B2', transitions = {IOSymbol('char','c'): Transition('A', output = [IOSymbol('char','z')])})])

test.run('A', [IOSymbol('char','a'), IOSymbol('char','c'), IOSymbol('char','b'), IOSymbol('char','c')])

print(test.decide('A', {IOSymbol('char','a'),IOSymbol('char','b')}))


test2 = DFA('A1',
            [State('A1', {IOSymbol('char','b'): Transition('B', [IOSymbol('char','b')])}),
             State('A2', {IOSymbol('char','b'): Transition('D', [IOSymbol('char','b')])}),
             State('B', {IOSymbol('char','a'): Transition('C', [IOSymbol('char','b')])}),
             State('C', {IOSymbol('char','a'): Transition('X', [IOSymbol('char','b')])}),
             State('D', {IOSymbol('char','a'): Transition('D', [IOSymbol('char','b')])}),
             State('X', {IOSymbol('char','a'): Transition('C', [IOSymbol('char','b')])})])


