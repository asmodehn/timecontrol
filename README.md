# timecontrol [![Build Status](https://travis-ci.org/asmodehn/timecontrol.svg?branch=master)](https://travis-ci.org/asmodehn/timecontrol)
Package providing time control capabilities to your (async) code.

The aim is to maximize the efficiency of long running code, and optimize machine use.
Although this cannot be a magic bullet, so we aim to follow a "best effort" strategy.

The main way to use the following concept is via decorators.
But there are/can be many other ways to use them, and we are always looking for better ways to integrate these in python.

## Control
A Control() instance maintains one set of command together, that should be called periodically, and often enough.
A OverLimiter triggers exception when a set of commands has gone a long time without being called, and Controller can take the appropriate action.

## Command
A Command() instance maintains exactly one command, that should not be called too often
A UnderLimiter triggers exception when a command was called too quickly, and Command can take the appropriate action.

## Internals

Internally there is only one schedule and only one log, conceptually, even if there may be multiple approximated 'views' of it.
Control put "TODO" items into the schedule (potentially repeated set of command run, enabling fuzzy runs, such as hypothesis strategies).
 There is an internal aioscheduler that pick from the (datetime-aware) schedule and organises them in the immediately available compute time.
Command log the (potentially throttled) calls passed to it and finished, and store them (in a pluggable storage - sqlite by default)

## Design Notes :

We aim to keep a duality / symmetry between log and schedule, between control and command, because they have complementary responsibilities.
Also mathematically, schedule and log are potentially infinite data structures => we should use a clean formal design for those (thinking about directed containers).

Internally everything is articulated around "events" which are immutable pieces of data.
Additional behavior (like learning from past calls, etc.) should be "pluggable" to capture copies of some events in between the controller and the command, in between the schedule and the log...

## ASync Notes :

These features are mostly useful in async model. To use a scheduler in usual sync mode, just have a look at Python `sched` module.
The UnderLimiter works in usual sync model, but will just block your controlflow.
Async model allows you to bypass the limits of only one controlflow, by running other coroutines "simultaneously", from the program point of view.

Note : We choose to not deal with threads here, as they usually bring more problems than they solve.
Instead we focus on maximising the usefulness of the one python thread via explicit async code scheduling.

## DISCLAIMER : Currently in development, not ready for prime time use just yet.
