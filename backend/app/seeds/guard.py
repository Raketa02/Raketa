"""The one refusal the seed system owns: production is never seeded.

Seed data is *fabricated*. It registers accounts whose password is written in
this repository's source, on addresses nobody owns, in states chosen to make a
screen easy to develop against. Every one of those properties is a virtue on a
laptop and a breach in production — an account with a public password is an
account anybody can sign in as.

**The refusal is a function of the settings object, and it is called on import**
(see ``app/seeds/__init__.py``). Putting it in the make target would leave it
where a container never looks: an image runs ``python -m app.seeds``, not
``make``. Putting it only in the runner would leave ``from app.seeds.catalog
import …`` as a way in. Importing anything from this package in production
fails, which is the smallest surface a guard can have.

The message names ``APP_ENV`` and lists what is permitted, and — the rule
``app/core/config.py`` states for its own refusals — it never echoes a
configured value. A seed run's output goes wherever the operator's terminal
goes, and the settings object beside this one holds a signing key and a database
password.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from app.core.config import Environment, Settings

#: Where seeding is permitted, written out per environment rather than derived
#: as "everything except production". Deriving it would make a fifth environment
#: seedable the moment somebody named it, which is the one wrong answer that is
#: invisible: nothing would fail, and the new environment would quietly accept
#: fabricated accounts. Written out, the day a fifth name exists is the day this
#: table stops covering `Environment` — and the check below refuses to import.
SEEDABLE: Mapping[Environment, bool] = MappingProxyType(
    {
        Environment.LOCAL: True,
        Environment.DEVELOPMENT: True,
        Environment.STAGING: True,
        Environment.PRODUCTION: False,
    }
)

_undecided = sorted(e.value for e in Environment if e not in SEEDABLE)
if _undecided:
    raise RuntimeError(
        "SEEDABLE does not say whether these environments may be seeded: "
        + ", ".join(_undecided)
        + ". Decide, rather than inheriting an answer."
    )

#: Spelled once, for the refusal message.
SEEDABLE_NAMES = ", ".join(env.value for env, allowed in SEEDABLE.items() if allowed)


class SeedRefused(RuntimeError):
    """Seeding was asked for somewhere it must not happen.

    A ``RuntimeError`` rather than a ``ValueError``, for the same reason
    ``ConfigurationError`` is one: nothing about this is a bad argument that a
    caller might sensibly catch alongside a parse failure. It is a refusal to
    proceed, and it should reach the operator.
    """


def refuse_unless_seedable(settings: Settings) -> None:
    """Raise unless ``settings`` selects an environment that may be seeded."""

    env = settings.APP_ENV
    if SEEDABLE[env]:
        return

    raise SeedRefused(
        f"Seeding is refused: APP_ENV selects '{env}'. Seed accounts are "
        f"fabricated and their password is public in this repository's source, "
        f"so an account seeded here is an account anybody can sign in as. "
        f"Seeding is permitted in: {SEEDABLE_NAMES}."
    )
