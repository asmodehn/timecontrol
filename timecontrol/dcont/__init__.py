"""
This package implements various directed containers in time dimension - not in state.
Meaning their structure is used for time management only.

We will here work in the RunTime Category:
- objects: atomic computation happening in time (space-state undefined at this level, but can be contained)
- morphism: time-translation between steps in computation

- product: parallel computation (run this and that, in this timestep)
- coproduct: probabilistic computation (run this OR that, not both)
- exponential: trigger the computation step

To keep things as clear as possible, the time interface is limited to :
- DSet/DMap (pointed -now- set in time) for the lower level (python or other) time management. This aim to encapsulate some state representation (TBD somewhere else)
- DDict (Directed tree in time) for the high level time management : each branch is a "possible" direction (coproduct in runtime category). each node store potential parallelism (product in runtime CAtegory)  realworld time passing will force choices to be made.
- DList (Directed list in time) for the high level time management : a log of what has been happening in the past.

Another module (scheduler) will be in charge of scheduling the current level consuming a ddict[??] and producing a dlist[dmap].
Note : No matter what kind of states your program wishes to express, time must always match with realworld time !

ddict[???] is a state representation of future possible (structured in state and time) computations => TODO : find clear and simple representation (hylang extension ?)
dlist[dmap] is a state representation of past computation, linearized as time is passing. the dmap is used to represent indeterminism of computation.

"""