"""The Challenges context — *asking somebody to play*, and nothing after it.

Settled by [#221](https://github.com/Raketa02/Raketa/issues/221). It is the
context the matcher has been citing since ``docs/adr/0098`` without being able to
name: ``matchmaking`` ends at a ranked list, and asking somebody begins here.

**Not ``matches``.** That word promises results, history and a played game, none
of which is in scope. **Not inside ``matchmaking``** either — the matcher reads
challenges through a port precisely so that it does not own them, which is why
nothing under this package imports it and nothing here may.

Its whole subject is the span between *send* and *everybody has answered*.
Nothing about when, where, money, results or the conversation itself belongs
here.

**One aggregate per game, with seats inside it.** A doubles send is one Challenge
containing four, not four challenges: three invariants span every seat at once —
the game is on only when the last seat accepts, an accepted player may cross the
net while their acceptance stands, and the arrangement travels as a unit — and
four aggregates would need a saga to answer *is it on*.

**The standing is derived from the seats and the clock, and never stored.** A
status column would be wrong for the whole gap between a deadline passing and a
sweep noticing, and it would be the copy that gets believed. ``standing.py``
holds the derivation; nothing in this module writes it down.

**Six events and no ``GameOn``.** Membership grows one acceptance at a time and
each acceptance is consequential the moment it happens — the chat a later context
opens starts with the second player and grows as the others arrive — so this
context publishes one event per acceptance and never a single *the challenge is
now on*. An event announcing a conclusion the fold already reaches would be a
second place for the standing to be true.
"""
