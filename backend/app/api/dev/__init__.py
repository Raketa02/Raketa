"""The dev console's surface: a gate and one roster path, and no page yet.

**Nothing in Play can be exercised with one phone** — a game that fills needs
other players saying yes. The console is the other players. Its first page, a
no-build ``console.html``, acted as another player by signing in as them through
the ordinary ``POST /api/v1/auth/login`` and pressed challenges; it went with the
challenges (#578). The games test console replaces it (``docs/adr/0194``, #590),
and acts as seed accounts without signing in. What is written below is what the
surface kept: the roster and its gate.

**The gate is checked on import of ``routes``, and deliberately not here.**
``app/seeds/`` puts its refusal in the package's ``__init__`` — the *smallest
surface a guard can have* — and that is the wrong shape for this one, for a
reason worth writing down because the tidier arrangement is an outage.
``app.main.create_app`` must read ``CONSOLE_SERVED`` in **every** environment to
decide whether to mount anything, and importing ``app.api.dev.gate`` executes
this file first. A refusal here would therefore make ``import app.main`` raise
in production: the deployable would crash at startup because it read its own dev
tool. So this package stays safe to import, ``gate`` raises only for a table
that has stopped covering ``Environment``, and the environment refusal sits at
the top of ``routes`` — the module that *is* the console, and the only one a
stray ``from app.api.dev.routes import …`` can reach.

**It declines the ``app/seeds/`` import it is entitled to.** Both are gated by
the same environments, so importing the catalog would be legal by construction
and would buy scenario names, rating bands and relationship labels for free. It
is refused for two reasons. Reading a row's meaning off its address rather than
off the catalog keeps ``catalog.py``'s promise — *"an account is named for the
state it represents"* — load-bearing, and keeps the cohort's hundreds of
unenumerated members first-class rows rather than a second, unlabelled class.
And structurally: ``app/seeds/__init__`` refuses on import too, so a console
that imported it would refuse in production for the *seed* table's reason, and
``CONSOLE_SERVED`` would be a second table nothing ever proved fires.
``tests/unit/test_dev_console_gate.py`` asserts the refusal that arrives is this
one, and ``.importlinter`` forbids the import outright.
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
