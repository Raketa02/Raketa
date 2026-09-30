"""The Proposals context: a game still filling, dealt to a pool's players.

Settled by ``docs/adr/0189`` §2 and §5 and specified in
``docs/specs/games-and-fill-in/the-mechanics.md`` §5–§7 (#538). A **Proposal** is
one event-sourced aggregate per proposed game — a pool, a sport, a kind, a court
hour at a club with no court number, the share fixed on it, the versions it was
dealt in, the yeses and the book-by — with two projections written in the act's
own transaction, the way ``groups``' are.

A **Pool** is the players who may be dealt a game plus the clubs whose courts
they may use, and it is first-class: every proposal carries its pool and nothing
here joins through a group. A group is the first kind of pool, filed under the
group's own id and opened by the first proposal made in it.

It reads six contexts and writes none of them, each through a port it declares
in its own words (``domain/ports.py``): **groups** for who is in a group's pool,
**clubs** for the court hour's share and book-by and a club's name, **blocks**,
the **Player profile** and **rating** for whether two people fit — judged by the
matcher's own pair rule, never a copy of it — and **payments** for whether a
player has a method their share could be charged to. It answers one demand back:
the live yeses ``payments`` asks about before a method is removed.

**What it does not do yet** is the engine that builds proposals (#540) and the
fill that books one (#541): ``MakeProposal`` and ``DealVersion`` are the use
cases the engine will drive, and seeds and tests drive them today.
"""
