"""Deterministic development data, created through the real write path.

Before this package, every row anybody developed against was made by hand —
through the API, or with ad-hoc SQL — so no two developers could reproduce each
other's screen, and nobody could reproduce their own after a ``make down -v``.

**Seeding executes the same use cases a request executes.** That is not tidiness.
The aggregates here are event-sourced with a transactional outbox, so a row
written straight into a table produces an aggregate with *no history*: it reads
correctly right up until something replays it, and then the seeded data and the
system's own account of that data disagree. It also skips every handler that
should have reacted. Going through the use cases means a seeded aggregate is
indistinguishable from one a player made, because it was made the same way.

The wiring comes from ``app.bootstrap.composition``, which is the composition
root the API uses — not a copy of it. A copied composition root keeps working
and stops being what production runs.

**The production guard is checked here, on import.** Not in the make target: a
make target is not what runs inside a container, and a guard that
``python -m app.seeds`` walks around is decoration. Importing *anything* from
this package runs it, because a submodule import executes this file first.
"""

from app.core.config import get_settings
from app.seeds.guard import (
    SEEDABLE,
    SEEDABLE_NAMES,
    SeedRefused,
    refuse_unless_seedable,
)

refuse_unless_seedable(get_settings())

__all__ = [
    "SEEDABLE",
    "SEEDABLE_NAMES",
    "SeedRefused",
    "refuse_unless_seedable",
]
