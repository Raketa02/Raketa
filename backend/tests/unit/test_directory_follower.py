"""The player directory's follower and rebuild (#793; ``docs/adr/0204`` §10),
over hand-written stand-ins for the two ports: an entry is written whole from
what the owners hold, and **an account the owners no longer know is forgotten**
— the deleted account's rows go, and its rest count on either side (#796).
Nothing in ``users`` disables an account today, so this is the seam that holds
it; the routes hold the rest (``tests/api/test_new_in_raketa.py``,
``tests/api/test_rows_stay_alive.py``)."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from datetime import datetime, timezone
from uuid import UUID

from app.kernel import Instant, instant
from app.modules.discovery.application.directory import (
    FollowTheDirectory,
    RebuildTheDirectory,
)
from app.modules.discovery.domain.directory import DirectoryEntry, PlayerFacts
from app.modules.discovery.domain.new_in_raketa import Joiner

EWA, GONE = UUID(int=1), UUID(int=2)
JOINED = instant(datetime(2026, 11, 1, 18, 0, tzinfo=timezone.utc))


def an_entry(player_id: UUID) -> DirectoryEntry:
    return DirectoryEntry(
        player_id=player_id,
        nickname="ewa",
        player=PlayerFacts(
            joined_at=JOINED,
            photo_id=None,
            area=None,
            tags=frozenset({"PLAYS_TO_WIN"}),
            open_to_new_people=True,
        ),
    )


class Owners:
    """What the owners hold: Ewa, and nothing about anybody else."""

    async def entry_of(self, player_id: UUID) -> DirectoryEntry | None:
        return an_entry(player_id) if player_id == EWA else None

    async def every_account(self) -> Sequence[UUID]:
        return (EWA, GONE)


class Directory:
    def __init__(self) -> None:
        self.entries: dict[UUID, DirectoryEntry] = {GONE: an_entry(GONE)}

    async def save(self, entry: DirectoryEntry) -> None:
        self.entries[entry.player_id] = entry

    async def forget(self, player_id: UUID) -> None:
        self.entries.pop(player_id, None)

    async def who_joined(
        self, *, after: Instant, leaving_out: Collection[UUID], limit: int | None = None
    ) -> tuple[Joiner, ...]:
        raise AssertionError("the writers never read the directory")


class Rests:
    """Who the rest count was told to forget."""

    def __init__(self) -> None:
        self.forgotten: list[UUID] = []

    async def came_on_screen(self, viewer, row, players, *, day) -> None:
        raise AssertionError("the writers report nothing")

    async def days_on_screen(self, viewer, row, players):
        raise AssertionError("the writers never read the count")

    async def forget(self, player_id: UUID) -> None:
        self.forgotten.append(player_id)


class Committed:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:  # pragma: no cover - never asked
        raise AssertionError("the rebuild never rolls back")


async def test_an_entry_is_written_from_what_the_owners_hold_and_a_gone_one_forgotten():
    directory, rests = Directory(), Rests()
    follower = FollowTheDirectory(sources=Owners(), directory=directory, rests=rests)

    await follower.execute(EWA)
    await follower.execute(GONE)
    await follower.execute(GONE)

    assert directory.entries == {EWA: an_entry(EWA)}
    # Ewa's count stands; the gone account's goes, on either side, each time.
    assert rests.forgotten == [GONE, GONE]


async def test_the_rebuild_writes_every_account_the_owners_know_and_commits_once():
    directory, rests, uow = Directory(), Rests(), Committed()
    rebuild = RebuildTheDirectory(
        sources=Owners(), directory=directory, rests=rests, uow=uow
    )

    rebuilt = await rebuild.execute()

    assert (rebuilt.accounts, rebuilt.entries) == (2, 1)
    assert directory.entries == {EWA: an_entry(EWA)}
    assert rests.forgotten == [GONE]
    assert uow.commits == 1
