"""The dev surface: the games test console's page, its roster, and the routes
the page presses (``docs/adr/0194``, #590).

**The refusal is the first import of this module**, and of every module of the
console (``refusal.py``), so importing it anywhere the console is not served
refuses before a router exists — and before the seed system the situations are
built from is reached, whose own refusal would otherwise arrive first.
``app/api/dev/__init__.py`` says why the refusal is not in the package's
``__init__``.

**The console acts as seed accounts without signing in** (ADR-0194 §2). A press
on a person's row names that person in its path — ``/dev/as/{player_id}/…`` —
and runs the use case their own button runs (``people.py``) — a club's,
``/dev/clubs/{club_id}/…``, the desk's (``club.py``); there is no token, no
session and no header a player route would honour, so the page holds and stores
nothing. The payment provider's controls are ``provider.py``'s, a group's board
``board.py``'s, the situations ``situations.py``'s, *Run it now*
``jobs.py``'s and a person's *Sent* pane ``sent.py``'s.

**The roster carries the password once, at the top level.** The console no
longer signs in with it; the **phone** does — the tester signs the protagonist in
with the address and the one public password every seeded account holds, which
``app/seeds/catalog.py`` decided *"so a developer signing in as any of them
types the same thing"*. It is public by construction — it is written in this
repository's source — and the gate, not secrecy, is what makes that safe.

**The data predicate is the seed system's own TLD** (``accounts.py``), imported
from the catalog now that the console is built from the seed's building blocks
(ADR-0194 §4), so there is one spelling of it. It is the roster's filter and the
acting account's refusal: **one rule, two uses** — the roster lists nobody the
console would refuse, and the console refuses everybody the roster leaves out.

**Its queries are its own, rather than read models in the contexts**, and that
is where this surface stands beside a documented rule instead of inside it.
*Dependencies point inward* fences the **domain and application** layers off the
ORM — ``.importlinter`` enforces exactly that — and ``app/api/`` has never been
on the inside of it. A port, an adapter and a use case per read would exist for
a development tool, and no request would ever run them. The trade, re-argued by
ADR-0194 rather than grown into: the whole surface is one directory that nothing
shipped imports, so deleting it changes nothing that ships; its reads are a few
columns and a ``WHERE`` each, over the projections the contexts already write;
and every **act** it takes is a context's own use case, never a write of its
own.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.dependencies import DbSession
from app.api.dev.accounts import seed_accounts_only
from app.api.dev.board import router as board_router
from app.api.dev.club import router as club_router
from app.api.dev.jobs import router as jobs_router
from app.api.dev.people import router as people_router
from app.api.dev.provider import router as provider_router
from app.api.dev.sent import router as sent_router
from app.api.dev.situations import router as situations_router
from app.modules.users.infrastructure.sqlalchemy_user_model import UserORM
from app.seeds.catalog import SEED_PASSWORD

#: The page: one file with no build (ADR-0194 §6).
CONSOLE_HTML = Path(__file__).resolve().parent / "console.html"


class RosterAccount(BaseModel):
    """One account the console may act as."""

    player_id: UUID = Field(
        ...,
        description=(
            "The id every player-surface read and write names this account by — "
            "and the one a console press names it by. Same value as the user's "
            "id — there is one identity."
        ),
    )
    email: str = Field(..., description="What the phone signs in with")
    nickname: str | None = Field(
        ...,
        description=(
            "The nickname, as every player surface says it (docs/adr/0199 §1). "
            "`null` for an account registered and never named, which no seed "
            "run leaves behind. What the account is *for* — the state it was "
            "named for — is read off the address, not the nickname."
        ),
    )


class RosterResponse(BaseModel):
    """Every account the console may act as, and the one password the phone
    signs in with."""

    password: str = Field(
        ...,
        description=(
            "The single password every seeded account holds — what the tester "
            "types into the phone to sign the protagonist in. **At the top "
            "level, never per account**: one password for all of them is the "
            "seed system's own decision, and a per-row copy would state the "
            "opposite. It is public in this repository's source; the environment "
            "gate, not secrecy, is what makes that safe."
        ),
    )
    accounts: list[RosterAccount] = Field(
        ...,
        description=(
            "Every account on the reserved seed TLD, ordered by address and "
            "**unpaginated**. An empty list is the honest answer in an unseeded "
            "database."
        ),
    )


dev_api_router = APIRouter(prefix="/dev", tags=["dev"])


@dev_api_router.get("", include_in_schema=False)
async def read_console() -> FileResponse:
    """The page. Out of the contract: a document describing how to fetch an
    HTML file is not something anything generates types from."""

    return FileResponse(CONSOLE_HTML, media_type="text/html")


@dev_api_router.get(
    "/roster",
    response_model=RosterResponse,
    status_code=status.HTTP_200_OK,
    summary="The accounts the console may act as, and the one password",
)
async def read_roster(db: DbSession) -> RosterResponse:
    rows = await db.execute(
        select(UserORM.id, UserORM.email, UserORM.nickname)
        .where(seed_accounts_only())
        .order_by(UserORM.email)
    )
    return RosterResponse(
        password=SEED_PASSWORD,
        accounts=[
            RosterAccount(
                player_id=row.id,
                email=row.email,
                nickname=row.nickname,
            )
            for row in rows
        ],
    )


dev_api_router.include_router(people_router)
dev_api_router.include_router(sent_router)
dev_api_router.include_router(club_router)
dev_api_router.include_router(provider_router)
dev_api_router.include_router(board_router)
dev_api_router.include_router(situations_router)
dev_api_router.include_router(jobs_router)
