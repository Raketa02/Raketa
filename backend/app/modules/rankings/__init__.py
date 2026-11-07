"""**Rankings** — a ranking per sport, sorted by the level
(``docs/adr/0203``; ``docs/specs/rankings/``).

A new bounded context that owns **the ranking projection and its reads**. It
records no event and has no aggregate: every row is a fold of one rating stream,
written when the rating's ``rating.moved_on_result`` is delivered through the
outbox, and rebuilt from the event store by the same fold.

**A stored projection, as a stated exception** to the backend's *derived, never
stored* (ADR-0203 §10): a page of General is a slice of an order over every
listed player, which no read could fold from every rating stream. The rating
stays the one owner of the level.

Each neighbour is reached through a port this context declares in its own words
(``domain/ports.py``), signed in ``infrastructure/`` and wired by the
composition root; Home reads the trophy's place through a port of its own,
signed in ``proposals/infrastructure/``, so nothing here knows its readers.
See ``.claude/rules/rankings.md``.
"""
