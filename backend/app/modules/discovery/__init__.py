"""**Discovery** — the people rows on Home: who is around the reader in Raketa
(``docs/adr/0204`` §10; ``docs/specs/home-rows/``).

A new bounded context that owns **the three people rows** — *Same competitive
level players*, *New in Rakieta* and *Same vibe players* — their See all reads,
and the stored copies they read. **New in Rakieta** is built (#793); the other
two read the same directory (#794, #795).

It records no event and has no aggregate. **The player directory** — one row
per account, a stated exception to the backend's *derived, never stored*
(ADR-0204 §10) — is written when a user's or a Player profile's event is
delivered through the outbox, by re-reading what the owners hold now, and
rebuilt from the event store by the same act. The profile stays the one owner
of the tags, the photographs, the area and the switch; ``users`` of the
nickname.

**Every neighbour is a port in this context's own words** (``domain/ports.py``),
signed in ``infrastructure/`` and wired by the composition root, so its domain
and application layers import no other context (``.importlinter``'s
*the-discovery-context-declares-its-own-ports*). See
``.claude/rules/discovery.md``.
"""
