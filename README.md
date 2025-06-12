# FINITY

finity is a programming language that compiles to a finite automaton. it achieves this by requiring that each variable have a known finite set of possible values,
then pretty much just running through every possible set of inputs and stopping if it finds a loop. because a compiled program is a finite automaton, rice's theorem
doesn't apply to it. this gives us desirable properties - you can determine whether an arbitrary finity program halts on a given input, you can optimise a finity
program *perfectly*, you can determine whether two finity programs have the same behaviour, etc. the downside is that for reasonably sized programs this requires a
great deal of computing power. this is a proof of concept, but a more sophisticated version might have real-world applications in cases like embedded systems, where
speed is important but it's easy to get access to a computer that's much more powerful than the one it'll be running on, or when a program will be run so often by so
many people that it's worth burning a lot of compute to make it more efficient.

### usage

finity.py exports `compile(filename, verbose = True)` and `optimise(FSM, verbose = True)`. both return an `FSM` object, which has a `run(start_state = State('start'))`
method. `compile` and `optimise` both return an `FSM` whose first state is `State('start')`, but this isn't guaranteed for `FSM`s constructed manually.

by default, for proof of concept purposes, all variable must be nonnegative integers less than four. this limit can be increased by adjusting `MAXINT` at the top of finity.py.
