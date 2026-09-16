"""The Matchmaking context — the stateful half of the matcher.

``docs/adr/0093`` splits the matcher in two. The arithmetic is an engine at
``app/engines/matchfit/``; everything that touches the world — the candidate
index, the ledgers, the search-side telemetry, the use cases and the routes — is
this module.

**Three boundaries, and only one of them is HTTP.** The public one carries
``openapi.player.json`` and the client's generated types; the module one is a use
case, and owns all the I/O; the **engine** one is a pure call and is the privacy
fence. Gating and candidate generation live here, where the I/O is; the engine
receives an already-gated, already-fenced set. Splitting the gates by kind —
*identity* outside, *arithmetic* inside — was rejected, because a fence with a
judgement call in it is not a fence.

The context arrives in pieces. What is here today is the half of the contract
that a ruleset is checked against — **the closed evidence vocabulary** — and the
half the matcher demands of everybody else: **the seven outward ports** in
``domain/ports.py``, each of which answers honestly whether or not its provider
exists (``docs/adr/0098``) — and today all but one have one.

**Five surfaces run the one pipeline and differ at the terminal stage**: the
shortlist, the two line-up surfaces, the deck, and since ``docs/adr/0174`` the
**reading** — ``POST /api/v1/radar``, ``domain/radar.py``,
``application/run_radar_reading.py``. A reading is the radar's request: every
player rated in the sport inside the viewer's own reach, five gates asked and
the other four **not asked**, no floor, no order but the printed distance and
then the id, a bearing and the sport chips on every row. It is a recorded
search and a prior disclosure like the deal, and **never a deal**: it enters no
dealt memory and notes no exposure, and the one number the deck's rule decides
on its envelope — *N want to play you* — is computed by the deck's own function
over the deck's own gates and ledgers, so the chip on either pane of Players is
one number.
"""
