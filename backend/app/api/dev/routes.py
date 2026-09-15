"""The dev surface: one roster, and the page that reads it.

**The gate is checked at the top of this module**, so importing it anywhere the
console is not served refuses before a router exists. ``app/api/dev/__init__.py``
says why the refusal is here and not in the package's ``__init__``.

It asks the **process's** settings, while ``create_app`` reads the table off the
settings it was handed — the same split ``app/seeds/`` has, where the package's
import checks the process and ``run`` re-checks the object that decides which
database is about to be written to. A process that is production does not get a
console by being handed a `Settings` that says otherwise.

**Two routes, and only one of them is the contract.** ``GET /dev`` hands over
``console.html`` and is ``include_in_schema=False``: a document describing how to
fetch a page is not something anything generates types from, and the claim
``openapi.dev.json`` makes is the honest one — this surface has exactly one path,
the roster, and every other request the console sends is a **player-surface**
request it makes as the player it signed in as.

**The roster carries the password once, at the top level.** The obvious shape —
``POST /dev/sessions {handle} → tokens`` — *is* an impersonation endpoint, and
this console refuses to have one; so the browser must present a credential to the
ordinary ``POST /api/v1/auth/login`` itself, which means it must hold one. One
password for every seeded account is what ``app/seeds/catalog.py`` decided *"so a
developer signing in as any of them types the same thing"*, and a per-account
copy would state the opposite. It is public by construction — it is written in
this repository's source — and ``guard.py``'s whole argument is that the gate,
not secrecy, is what makes that safe.

**The data predicate is a filter, and never a refusal.** ``is_seed_account`` is
the roster's query and nothing else. Making the console *refuse* a non-seed
address would be theatre: it signs in through the ordinary login route, which
any browser already reaches with any credential. So *gated structurally and by
data* resolves asymmetrically — the structural gate is a check, and the data gate
is a **consequence**: production has no addresses on the reserved TLD, so the
roster is empty there by construction. Both hold; only one of them can fail.

**The query is this module's own, rather than a read model on ``users``**, and
that is the one place this surface stands beside a documented rule instead of
inside it. *Dependencies point inward* fences the **domain and application**
layers off the ORM — `.importlinter` enforces exactly that — and `app/api/` has
never been on the inside of it. What the rule would otherwise ask for here is a
port, an adapter and a use case in the `users` context, all of which would exist
for a development tool and none of which any request would ever run. The trade
taken instead: the whole dev surface is one directory nothing else imports, its
one query is three columns and a `WHERE`, and the day it is deleted nothing
shipped changes shape. If it ever grows a second query it has become a product,
and the placement is re-argued rather than grown into.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.sql.elements import ColumnElement

from app.api.dependencies import DbSession
from app.api.dev.gate import refuse_unless_served
from app.core.config import get_settings
from app.modules.users.infrastructure.sqlalchemy_user_model import UserORM

refuse_unless_served(get_settings())

CONSOLE_HTML = Path(__file__).resolve().parent / "console.html"

#: A seed account is one addressed on a TLD RFC 2606 §2 reserves: no registry
#: will ever sell a name under it, so an address here cannot be somebody's real
#: mailbox. **Spelled again rather than imported** from ``app/seeds/catalog.py``
#: — see the package docstring for why this surface declines that import — and
#: ``tests/unit/test_dev_console_surface.py`` is what keeps the two spellings
#: equal, so the second one cannot drift or be deleted as duplication.
SEED_ADDRESS_TLD = ".example"

#: The one public password every seeded account holds. Spelled again for the same
#: reason, and pinned to the catalog's by the same test.
SEED_PASSWORD = "raketa-seed1"


def is_seed_account(email: str) -> bool:
    """Is this address a fabricated one?

    Total: a string with no ``@`` has no domain, so it is **not** a seed account
    rather than an error — this is a filter, and a filter has an answer for every
    row it is shown. The ``@`` is checked rather than assumed: without it
    ``rpartition`` hands back the whole string, and ``nonsense.example`` would
    read as an address on the reserved TLD.

    The roster's rule, and nothing else's — ``seed_accounts_only`` below is the
    same rule in SQL and is what the query runs. The console is deliberately not
    built to *refuse* a non-seed address, because that would be theatre: it signs
    in through the ordinary login route, which any browser already reaches with
    any credential.
    """

    local, at, domain = email.rpartition("@")
    return bool(local) and bool(at) and domain.casefold().endswith(SEED_ADDRESS_TLD)


def seed_accounts_only() -> ColumnElement[bool]:
    """``is_seed_account`` written in SQL, over ``UserORM.email``.

    Two spellings of one predicate, because the roster must not load a real
    database's users into this process to filter them — and they cannot drift
    far, since the domain is everything after the last ``@`` and an address ends
    where its domain does, so a case-insensitive suffix match is the same claim.
    The ``%@%`` is the ``@`` the Python side checks for, and it is here for the
    same reason: without it the pattern matches a string that is not an address
    at all. ``tests/api/test_dev_console.py`` registers addresses on both sides
    of the line and asserts the two agree.
    """

    return UserORM.email.ilike(f"_%@%{SEED_ADDRESS_TLD}")


class RosterAccount(BaseModel):
    """One account the console may sign in as."""

    player_id: UUID = Field(
        ...,
        description=(
            "The id every player-surface read and write names this account by. "
            "Same value as the user's id — there is one identity."
        ),
    )
    email: str = Field(..., description="What the console types into `/auth/login`")
    name: str | None = Field(
        ...,
        description=(
            "The whole name, as every player surface says it. `null` for an "
            "account registered and never named, which no seed run leaves "
            "behind. What the account is *for* — the state it was named for — is "
            "read off the address, not the name: the roster reads meaning off "
            "the address rather than out of the seed catalog."
        ),
    )
    nickname: str | None = Field(
        ...,
        description=(
            "The handle, drawn as `@nickname` on a record and the You tab only. "
            "`null` exactly when `name` is: the naming is one act carrying both."
        ),
    )


class RosterResponse(BaseModel):
    """Every account the console may act as, and the one password that does it."""

    password: str = Field(
        ...,
        description=(
            "The single password every seeded account holds. **At the top level, "
            "never per account**: one password for all of them is the seed "
            "system's own decision, and a per-row copy would state the opposite. "
            "It is public in this repository's source; the environment gate, not "
            "secrecy, is what makes that safe."
        ),
    )
    accounts: list[RosterAccount] = Field(
        ...,
        description=(
            "Every account on the reserved seed TLD, ordered by address and "
            "**unpaginated** — the console filters client-side. An empty list is "
            "the honest answer in an unseeded database, and the only answer "
            "possible in one holding real players."
        ),
    )


dev_api_router = APIRouter(prefix="/dev", tags=["dev"])


@dev_api_router.get(
    "/roster",
    response_model=RosterResponse,
    status_code=status.HTTP_200_OK,
    summary="The accounts the console may act as, and the one password",
)
async def read_roster(db: DbSession) -> RosterResponse:
    rows = await db.execute(
        select(UserORM.id, UserORM.email, UserORM.name, UserORM.nickname)
        .where(seed_accounts_only())
        .order_by(UserORM.email)
    )
    return RosterResponse(
        password=SEED_PASSWORD,
        accounts=[
            RosterAccount(
                player_id=row.id,
                email=row.email,
                name=row.name,
                nickname=row.nickname,
            )
            for row in rows
        ],
    )


@dev_api_router.get("", include_in_schema=False)
async def read_console() -> FileResponse:
    return FileResponse(CONSOLE_HTML, media_type="text/html")
