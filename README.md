# timecontrol [![Build Status](https://travis-ci.org/asmodehn/timecontrol.svg?branch=master)](https://travis-ci.org/asmodehn/timecontrol)
Package providing time control capabilities to your (async) code.

The aim is to maximize the efficiency of long running code, and optimize machine use.
Although this cannot be a magic bullet, so we aim to follow a "best effort" strategy.

The main way to use the following concept is via decorators.
But there are/can be many other ways to use them, and we are always looking for better ways to integrate these in python.

## Design

Although we started with quite a complex design, this one has been greatly simplified to fit more tightly to the pythonic way of doing things.
We should still refer to the "functional"/"type as behavior"/"actor" perspective, but at the "outside interface" of the program (logger, DB storage, etc.)
On the inside (profiling, how eventloops schedule tasks, optimizing call times, etc. should remain usual python)

## ASync Notes :

These features are mostly useful in async model.
So we choose to not deal with threads here, as they usually bring more problems than they solve.
Instead we focus on maximising the usefulness of the one python thread via explicit async code scheduling.

## DISCLAIMER : Currently in development, not ready for prime time use just yet.
