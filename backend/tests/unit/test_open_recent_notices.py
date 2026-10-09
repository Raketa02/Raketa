"""**Opening the recent notices** (#621; the mechanics Q101): the visit is
recorded on the player's bell and committed — and a second phone opening the
list at the same moment, which collides on the bell's stream, is no error: that
visit stands.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.application.events import EventStreamVersionConflict
from app.modules.notifications.application.opening import OpenRecentNotices
from app.modules.notifications.domain.bell import Bell
from tests.unit.fake_clock import MovableClock

NOW = datetime(2026, 10, 9, 10, tzinfo=timezone.utc)


class StandInBells:
    def __init__(self, *, colliding: bool = False) -> None:
        self.colliding = colliding
        self.saved: list[Bell] = []
        self._streams: dict[UUID, list] = {}

    async def load(self, player_id: UUID) -> Bell:
        return Bell.from_history(player_id, self._streams.get(player_id, []))

    async def save(self, bell: Bell) -> None:
        if self.colliding:
            raise EventStreamVersionConflict("another phone opened it first")
        self._streams.setdefault(bell.player_id, []).extend(bell.pull_events())
        self.saved.append(bell)


class StandInUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


def opening(bells: StandInBells, uow: StandInUnitOfWork) -> OpenRecentNotices:
    return OpenRecentNotices(bells=bells, uow=uow, clock=MovableClock(NOW))


async def test_opening_the_list_records_the_visit_and_commits_it():
    bells, uow = StandInBells(), StandInUnitOfWork()
    player = uuid4()

    await opening(bells, uow).execute(player)

    assert (await bells.load(player)).last_opened_at == NOW
    assert uow.commits == 1


async def test_opening_it_again_at_the_same_moment_writes_nothing():
    bells, uow = StandInBells(), StandInUnitOfWork()
    player = uuid4()
    await opening(bells, uow).execute(player)

    await opening(bells, uow).execute(player)

    assert len(bells.saved) == 1
    assert uow.commits == 1


async def test_a_phone_colliding_with_another_s_visit_is_no_error():
    bells, uow = StandInBells(colliding=True), StandInUnitOfWork()

    await opening(bells, uow).execute(uuid4())

    assert (uow.commits, uow.rollbacks) == (0, 1)
