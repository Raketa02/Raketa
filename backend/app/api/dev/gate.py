"""Where the dev console is served, written out per environment.

**A second table, not ``SEEDABLE``.** It answers the same today and it is not
the same question, and ``app/seeds/guard.py``'s own comment is the argument
against deriving one refusal from another: derive it, and the day somebody names
a fifth environment nothing fails and the new environment quietly serves a
console. Two tables means the day a fifth name exists is the day *both* stop
covering ``Environment`` — and both refuse to import.

**Safe to import anywhere.** This module raises only for a table that has
stopped covering the enum; the environment refusal is a function you call.
``app.main.create_app`` imports it unconditionally and imports the router only
inside the ``if``, because a module that raises on import cannot also be the
thing that decides whether to import it — a production deployable that crashes
at startup because it read its own dev tool is not a gate, it is an outage.

The message names ``APP_ENV`` and lists what is permitted, and — the rule
``app/core/config.py`` states for its own refusals — it never echoes a
configured value. The settings object beside this one holds a signing key and a
database password.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from app.core.config import Environment, Settings

#: Where the dev console is served, written out per environment rather than
#: derived as "everything except production". Deriving it would serve the
#: console in a fifth environment the moment somebody named one, which is the
#: one wrong answer that is invisible: nothing would fail, and a page offering
#: to sign in as other accounts would appear somewhere nobody decided about.
CONSOLE_SERVED: Mapping[Environment, bool] = MappingProxyType(
    {
        Environment.LOCAL: True,
        Environment.DEVELOPMENT: True,
        Environment.STAGING: True,
        Environment.PRODUCTION: False,
    }
)

_undecided = sorted(e.value for e in Environment if e not in CONSOLE_SERVED)
if _undecided:
    raise RuntimeError(
        "CONSOLE_SERVED does not say whether the dev console is served in these "
        "environments: "
        + ", ".join(_undecided)
        + ". Decide, rather than inheriting an answer."
    )

#: Spelled once, for the refusal message.
CONSOLE_SERVED_NAMES = ", ".join(
    env.value for env, served in CONSOLE_SERVED.items() if served
)


class ConsoleRefused(RuntimeError):
    """The dev console was reached somewhere it must not be served.

    A ``RuntimeError`` rather than a ``ValueError``, for the reason
    ``SeedRefused`` is one: nothing about this is a bad argument a caller might
    sensibly catch alongside a parse failure. It is a refusal to proceed, and it
    should reach the operator.
    """


def refuse_unless_served(settings: Settings) -> None:
    """Raise unless ``settings`` selects an environment the console is served in."""

    env = settings.APP_ENV
    if CONSOLE_SERVED[env]:
        return

    raise ConsoleRefused(
        f"The dev console is refused: APP_ENV selects '{env}'. It hands a browser "
        f"a roster of accounts and one password that signs in as any of them, so "
        f"it is a development tool and never a deployed surface. It is served "
        f"in: {CONSOLE_SERVED_NAMES}."
    )
