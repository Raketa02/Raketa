"""The migration chain, walked the way ``alembic upgrade head`` walks it.

**A revision id and a filename are two different names, and only one of them is
the link.** ``0020_the_conversation_room.py`` says so in its own docstring — *the
filename carries the sentence; the id only has to be unique* — and then pointed
its ``down_revision`` at the file above it rather than at that file's id. Alembic
resolves the chain lazily, so nothing failed until a container came up: the API
restarted forever on ``KeyError: '0019_the_searchers_own_area'`` with a healthy
database beside it, and every path that needs a schema — ``make up``, ``make
migrate``, ``make seed`` — was down for as long as it took somebody to read a
stack trace.

**Nothing else in this repository walks it.** The suite runs on SQLite built from
``Base.metadata``, which is the right trade for a test suite and is also why the
migrations can rot without a single test going red. This is the cheapest possible
guard against that: build the map alembic builds, and ask it for one head.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

#: The repository's own ``alembic.ini``, found from this file rather than from
#: the working directory: ``make check`` runs pytest from ``backend/`` and a
#: developer may not.
ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


@pytest.fixture(scope="module")
def scripts() -> ScriptDirectory:
    return ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))


def test_every_migration_names_one_that_exists(scripts: ScriptDirectory) -> None:
    """*Each ``down_revision`` is a revision id somebody wrote, not a filename.*

    Asserted by name rather than by letting ``walk_revisions`` raise, because the
    exception alembic raises for this is a ``KeyError`` with a string in it and
    the person meeting it is looking at a container that will not start.
    """

    known = {script.revision for script in scripts.walk_revisions()}
    dangling = {
        script.revision: script.down_revision
        for script in scripts.walk_revisions()
        if script.down_revision is not None and script.down_revision not in known
    }

    assert not dangling, (
        f"{dangling} name a previous revision that does not exist. A "
        f"``down_revision`` is the id at the top of the other file — the value "
        f"of its ``revision =`` — and never its filename."
    )


def test_the_chain_has_exactly_one_head(scripts: ScriptDirectory) -> None:
    """*There is one ``head``, so ``upgrade head`` is unambiguous.*

    Two heads is what a merge produces when two branches each add a migration on
    top of the same one, and alembic refuses to upgrade to an ambiguous head
    rather than picking.
    """

    assert len(scripts.get_heads()) == 1, scripts.get_heads()
