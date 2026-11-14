"""``python -m app.modules.discovery.infrastructure.rebuild_cli`` — the rebuild.

What ``make discovery-rebuild`` runs: every directory entry written from every
account the event store holds (#793; ``docs/adr/0204`` §10), so the players
who joined before the directory shipped are on its rows, each with their real
*joined* — and then every current level from every rating stream (#794), so the
players rated before the levels shipped are compared. **The same acts the
delivery runs** — ask the owners, write the entry whole — so a rebuild writes
what live delivery wrote, and running it twice changes nothing.

A one-shot command rather than a job: it is owed once, the day the directory
(migration 0073) or the levels (0074) ship to a store that already holds
players, and every change after that reaches them through the outbox.
``docs/adr/0092``'s register is for loops. Thin on purpose — the use case
comes out of the composition root, so it walks the store a request does — and
under ``app/`` because the container image copies ``app/`` and not
``scripts/``.
"""

from __future__ import annotations

import asyncio

from app.bootstrap.composition import (
    build_background_session_factory,
    build_rebuild_the_directory,
    build_rebuild_the_levels,
)
from app.core.config import get_settings
from app.infrastructure.database.engine import create_engine
from app.modules.discovery.application.directory import Rebuilt
from app.modules.discovery.application.levels import LevelsRebuilt


async def rebuild() -> tuple[Rebuilt, LevelsRebuilt]:
    engine = create_engine(get_settings())
    try:
        async with build_background_session_factory(engine)() as session:
            directory = await build_rebuild_the_directory(session).execute()
            levels = await build_rebuild_the_levels(session).execute()
            return directory, levels
    finally:
        await engine.dispose()


def main() -> int:
    directory, levels = asyncio.run(rebuild())
    print(
        f"Player directory rebuilt: {directory.entries} entr(ies) written from "
        f"{directory.accounts} account(s); {levels.levels} current level(s) "
        "written from the ratings."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
