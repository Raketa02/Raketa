"""Importing this refuses, unless the console is served here.

**Every module of the console imports it first** — before anything else from the
application — and ``gate`` and the package's ``__init__`` are the only two that
do not, because ``create_app`` reads the gate in every environment
(``app/api/dev/__init__.py`` says why that matters). So there is no order of
imports that reaches a console route, or the seed system the situations are
built from, before the console's own refusal has run: the error that arrives
is ``ConsoleRefused`` — never the seed system's ``SeedRefused`` in production,
and never silence in development or staging, where the seed may run
(``docs/adr/0194`` §1, §4). ``tests/unit/test_dev_console_gate.py`` imports every
module of the package under each of those environments and asserts exactly
that.

It asks the **process's** settings, while ``create_app`` reads the table off the
settings it was handed — the same split ``app/seeds/`` has, where the package's
import checks the process and ``run`` re-checks the object that decides which
database is about to be written to. A process that is production does not get a
console by being handed a ``Settings`` that says otherwise.
"""

from app.api.dev.gate import refuse_unless_served
from app.core.config import get_settings

refuse_unless_served(get_settings())
