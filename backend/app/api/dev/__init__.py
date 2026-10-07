"""The dev console's surface: the **games test console** (``docs/adr/0194``,
#590).

**Testing the new games by hand means being several people at once** — a game
fills when four people have said yes, a club answers a request, a card declines.
The console is the other people: a page served by the local backend that the
tester opens on the laptop while the phone is signed in as the protagonist. It
**acts as seed accounts without signing in** — each press names the account in
its path and runs that person's own use case (``people.py``), or the club's
(``club.py``) — steers the in-process payment provider (``provider.py``), shows
a group's people and games (``board.py``), sets the stage for a mechanic in one
press (``situations.py``), runs a timed rule's job over what is due
(``jobs.py``) and shows who was told what — each person's notices, pushes and
emails (``sent.py``). It is served in ``local`` only (``gate.py``).

**The gate is read here, and the refusal is not.** ``app/seeds/`` puts its
refusal in the package's ``__init__`` — the *smallest surface a guard can have*
— and that is the wrong shape for this one, for a reason worth writing down
because the tidier arrangement is an outage. ``app.main.create_app`` must read
``CONSOLE_SERVED`` in **every** environment to decide whether to mount anything,
and importing ``app.api.dev.gate`` executes this file first. A refusal here
would therefore make ``import app.main`` raise in production: the deployable
would crash at startup because it read its own dev tool. So this package and
``gate`` stay safe to import, and **every other module of it imports
``refusal.py`` first** — the module whose import is the refusal.

**It imports the seed system now** (ADR-0194 §4): situations are built from the
seed's building blocks, and the seed's own constants — the reserved TLD, the
one password, the protagonist — are imported rather than spelled twice. The old
console declined that import so that the refusal arriving in production was its
own and not ``SeedRefused``; the order of imports holds that now, and
``tests/unit/test_dev_console_gate.py`` imports every module of the package
under every environment the console is not served in and asserts the console's
own refusal is the one that arrives.
"""

from app.api.dev.gate import (
    CONSOLE_SERVED,
    CONSOLE_SERVED_NAMES,
    ConsoleRefused,
    refuse_unless_served,
)

__all__ = [
    "CONSOLE_SERVED",
    "CONSOLE_SERVED_NAMES",
    "ConsoleRefused",
    "refuse_unless_served",
]
