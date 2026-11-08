"""``python -m app.modules.rankings.infrastructure.rebuild_cli`` — the rebuild.

What ``make rankings-rebuild`` runs: every ranking row and every level-history
point folded from every rating stream the event store holds (#768, #769;
``docs/adr/0203`` §10), so the players who played before the ranking shipped
are on it, with a real week behind their chips — and every rated player's
*Show me in General* read off their profile (#772), so a projection rebuilt
from nothing lists no hidden player. **The same fold the delivery
runs**, so a rebuild writes what live delivery wrote, and running it twice
changes nothing.

A one-shot command rather than a job: it is owed once, the day the ranking
ships to a store that already holds results, and every result after that
reaches its row through the outbox. ``docs/adr/0092``'s register is for loops.
Thin on purpose — the use case comes out of the composition root, so it walks
the store a request does — and under ``app/`` because the container image
copies ``app/`` and not ``scripts/``. **It forgets every sport's kept General
order in the ephemeral store the API reads** (#770), so the next read works
the rebuilt rows out; a store it cannot reach is told nothing, and an order
held there lasts its minute.
"""

from __future__ import annotations

import asyncio

from app.bootstrap.composition import (
    build_background_session_factory,
    build_general_orders,
    build_rebuild_the_rankings,
)
from app.core.config import get_settings
from app.infrastructure.database.engine import create_engine
from app.infrastructure.redis_client import create_redis_client
from app.modules.rankings.application.projection import Rebuilt


async def rebuild() -> Rebuilt:
    settings = get_settings()
    engine = create_engine(settings)
    store = create_redis_client(settings)
    try:
        async with build_background_session_factory(engine)() as session:
            return await build_rebuild_the_rankings(
                session, orders=build_general_orders(store)
            ).execute()
    finally:
        # See ``redis_client.close_redis`` for the ignore.
        await store.aclose()  # type: ignore[attr-defined]
        await engine.dispose()


def main() -> int:
    rebuilt = asyncio.run(rebuild())
    print(
        f"Rankings rebuilt: {rebuilt.rows} row(s) folded from "
        f"{rebuilt.ratings} rating stream(s), {rebuilt.points} new "
        f"level-history point(s), {rebuilt.switches} player(s)' Show me in "
        f"General followed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
