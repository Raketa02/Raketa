"""The dev console: a tool that answers back, made of one file and one path.

**Nothing in Play can be exercised with one phone.** ``Line-up incomplete``, the
decline that reopens a seat, the instant match born of a mutual yes — every one
of them needs a real second player answering. This is the second player.

**It acts as another player by signing in as them**, through the ordinary
``POST /api/v1/auth/login`` with the seed password that already exists as one
public constant. There is no impersonation endpoint, no ``Act-As`` header and no
authorisation path that exists for this tool. The consequence is the good one:
every write the console presses is a *player-surface* write, so *acts as another
player* is literal rather than approximate.

**Nothing here reacts on its own.** There are no auto-reply timers of any kind.
The prototype's simulated replies are machinery the UI spec §G4 lists for
deletion, and it is explicit that *"acceptance is not instant and may never
arrive — the interface must handle pending indefinitely."* The console exists so
that a human decides when the other side answers; a timer here would put the
prototype's lie back, one layer down.

**Made of one no-build HTML file** returned by a ``FileResponse``. No npm, no
bundler, no codegen, and no lint lane for one file — said here so that nobody
adds one. This is not a detail beside the placement under ``backend/``; it is
what makes the placement true. The job is a table and a few buttons. The day it
wants a component tree it has become a product, and the placement is re-argued
rather than grown into.

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
