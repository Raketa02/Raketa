"""``python -m app.modules.rankings.infrastructure.rebuild_cli`` — the rebuild.

What ``make rankings-rebuild`` runs: every ranking row folded from every rating
stream the event store holds (#768; ``docs/adr/0203`` §10), so the players who
played before the ranking shipped are on it. **The same fold the delivery
runs**, so a rebuild writes what live delivery wrote, and running it twice
changes nothing.

A one-shot command rather than a job: it is owed once, the day the ranking
ships to a store that already holds results, and every result after that
reaches its row through the outbox. ``docs/adr/0092``'s register is for loops.
Thin on purpose — the use case comes out of the composition root, so it walks
the store a request does — and under ``app/`` because the container image
copies ``app/`` and not ``scripts/``.
"""

from __future__ import annotations

import asyncio

from app.bootstrap.composition import (
    build_background_session_factory,
    build_rebuild_the_rankings,
)
from app.core.config import get_settings
from app.infrastructure.database.engine import create_engine
from app.modules.rankings.application.projection import Rebuilt


async def rebuild() -> Rebuilt:
    engine = create_engine(get_settings())
    try:
        async with build_background_session_factory(engine)() as session:
            return await build_rebuild_the_rankings(session).execute()
    finally:
        await engine.dispose()


def main() -> int:
    rebuilt = asyncio.run(rebuild())
    print(
        f"Rankings rebuilt: {rebuilt.rows} row(s) folded from "
        f"{rebuilt.ratings} rating stream(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
