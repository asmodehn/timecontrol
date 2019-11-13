# timecontrol
Package providing time control capabilities to your async code.

There are multiple ways to use them (as decorators, or other python constructs).

## Control
The aim is to maximize the precision, on whatever machine, with whatever load.
Although this cannot be a magic bullet, so we aim to follow a "best effort" strategy.

Limiter is supposed to slow things down, whereas scheduler is supposed to speed things up, relatively to a defined period.


## Limiter :
This limits your capacity to call a function too often, implicitely.
It basically sleeps until the appropriate time has passed

## Scheduler :  
This gives you the possibility to call a function often, implicitely.
It basically loops when the appropriate time has passed.

Note : This is not symmetrical to the limiter, because of the inherent python behavior (like most programming languages) to call a function as soon as possible.

## ASync :
These are mostly useful in async model.
The limiter works in usual sync model, but will just block your controlflow.
Async model allows you to bypass the limits of only one controlflow, by running other coroutines simultaneously.

Note : We choose to not deal with threads here, as they usually bring more problems than they solve.

## DISCLAIMER : Currently in development, not ready for prime time use just yet.

### TODO : documentation...