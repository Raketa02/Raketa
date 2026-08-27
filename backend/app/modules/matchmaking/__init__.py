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
that a ruleset is checked against: **the closed evidence vocabulary**.
"""
