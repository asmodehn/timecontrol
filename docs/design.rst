Design
======

TimeControl is aiming at simplifying time management for your program, to slow it down or speed it up when necessary.
This can be quite tricky to understand and actually implement, so we have split our code into many parts for everyone's understanding.

Note : this is not a target for optimisation, it is targeted for usually "slow running programs" that want to provide other garantees (stability, eventuel convergence, etc.)

We take a step back from traditional imperative programming :
- do this
- then do that
- and then that

And from traditional functional programming as well:
- compute and give me this
- then compute and give me that
- etc.

Instead we focus on on intent and events, on expectations, and actual facts, and we time everything reasonably.


On one axis we have intents and events, roughly corresponding on what will be acted upon, or what has been percieved:

events ---> Subject (human - program) ---> intents


On another axis we have :

World where we *think* we control ( environment on which we made expactations and have been able to maintain them - potentially via actions)
 |
Subject (human - program)
 |
World where we *think* we do not control (environment on which we havent yet made any expectations)


Events and Intents are kept in time-indexed "logs"/"schedules".
Note there can be Events expected in the future (no materialization yet), and Intents in the past (no realization yet)


The controlled world can be controlled (from the Subject perspective) via "Commands" that he can call, and expect a return.
Note these commands could be pure functions (if we found their result matched our intent in the past) -> memoizing -> optimizations

Both controlled and uncontrolled world are observed by "Results"

The uncontrolled world can attempt to control the subject via a "Controller" requesting some sort of progress over time, usually via the action on intent to verify expectations...




Validation
----------

To validate our design, we need a long-running agent, operating on a simple system, and show that it is able to learn complex operations without previous knowledge.

External system : basic integer arithmetic (+ and *)
Internal system : Peano arithmetic (ZERO and SUCC)
Goal : find peano algorithms for + and *
Alternative : Dual numbers (find some way to compare actual derivative with behavior of the learning...)



