"""The directory's two writers: **the follower**, on every delivered user or
Player profile event that changes what a row reads, and **the rebuild**, over
every account (``docs/adr/0204`` §10).

**Both ask the owners the same question** — what does this account hold now
(``DirectorySources.entry_of``) — and write the answer whole. So a redelivery
writes the same entry and changes nothing, a delivery out of order writes what
the owners hold, and the rebuild writes what live delivery did, entry for
entry. An account the owners no longer know — disabled, the one way an account
goes today — is forgotten, its tags with it.

**No commit** in the follower: the transaction is the delivery's. The rebuild
is a command-line run of its own and commits once at the end
(``infrastructure/rebuild_cli.py``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.modules.discovery.domain.ports import DirectorySources, PlayerDirectory


async def _write(
    sources: DirectorySources, directory: PlayerDirectory, player_id: UUID
) -> bool:
    entry = await sources.entry_of(player_id)
    if entry is None:
        await directory.forget(player_id)
        return False
    await directory.save(entry)
    return True


@final
class FollowTheDirectory:
    """An owner's event was delivered, so its account's entry is written again
    from what the owners hold now."""

    def __init__(
        self, *, sources: DirectorySources, directory: PlayerDirectory
    ) -> None:
        self._sources = sources
        self._directory = directory

    async def execute(self, player_id: UUID) -> None:
        await _write(self._sources, self._directory, player_id)


@final
@dataclass(frozen=True, slots=True)
class Rebuilt:
    #: Accounts the store holds a stream for.
    accounts: int
    #: Entries written: every account the owners still know.
    entries: int


@final
class RebuildTheDirectory:
    """Every entry, written from every account the event store holds — so the
    players who joined before the directory shipped are on its rows. Running
    it twice changes nothing."""

    def __init__(
        self,
        *,
        sources: DirectorySources,
        directory: PlayerDirectory,
        uow: UnitOfWork,
    ) -> None:
        self._sources = sources
        self._directory = directory
        self._uow = uow

    async def execute(self) -> Rebuilt:
        accounts = 0
        entries = 0
        for player_id in await self._sources.every_account():
            accounts += 1
            if await _write(self._sources, self._directory, player_id):
                entries += 1
        await self._uow.commit()
        return Rebuilt(accounts=accounts, entries=entries)
