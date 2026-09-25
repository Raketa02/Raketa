"""What the Club context needs from the outside world.

**Each repository writes the search projection in the caller's transaction.**
A club's projection is what home-club search and join search read, and a club
edit must be visible to the next search rather than *eventually*
(``docs/adr/0182`` §2) — so ``save`` appends to the stream, enqueues the events
on the outbox and writes the row, all in the unit of work the use case commits,
and there is no second step a caller could forget. The same holds for the
account's row, which is what sign-in and every club request read.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable
from uuid import UUID

from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.club_account import ClubAccount
from app.modules.users.domain.value_objects import Email


@runtime_checkable
class ClubRepository(Protocol):
    async def load(self, club_id: UUID) -> Optional[Club]:
        """The club as its stream tells it, or ``None`` for a stream that does
        not exist. Its version is what the next ``save`` expects."""
        ...

    async def save(self, club: Club) -> None:
        """Append what the club recorded, enqueue it, and write its search row —
        in the caller's transaction, and without committing it."""
        ...


@runtime_checkable
class ClubAccountRepository(Protocol):
    async def get_by_id(self, account_id: UUID) -> Optional[ClubAccount]:
        """The account, **read from its row**, which is the read every club
        request pays (``docs/adr/0185`` §7). The row carries no stream version,
        so an account read here is saved at version zero and a second write to
        an existing stream is refused as a concurrent one rather than lost."""
        ...

    async def get_by_email(self, email: Email) -> Optional[ClubAccount]:
        """The account that signs in with this email, **among club accounts
        only** — a User holding the same address is somebody else."""
        ...

    async def save(self, account: ClubAccount) -> None:
        """Append what the account recorded, enqueue it, and write its row — in
        the caller's transaction, and without committing it."""
        ...
