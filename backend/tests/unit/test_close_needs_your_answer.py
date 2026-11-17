"""**Closing Needs your answer** (#815; ``docs/adr/0205`` §3): the visit is
recorded on the player's stream and committed. **Two phones closing at once**
collide on that stream: the one that lost reads the other's visit and closes
once more, so a newer watermark is never lost to an older one — and a visit
with nothing it showed records nothing.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.application.events import EventStreamVersionConflict
from app.kernel import instant
from app.modules.proposals.application.needs_your_answer import CloseNeedsYourAnswer
from app.modules.proposals.domain.events import NeedsYourAnswerClosed
from app.modules.proposals.domain.needs_your_answer import NeedsYourAnswerVisit
from tests.unit.fake_clock import MovableClock

NOW = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
#: The newest arrival the other phone's sheet showed.
THEIRS = NOW - timedelta(minutes=10)
#: The newest arrival this phone's sheet showed: newer.
MINE = NOW - timedelta(minutes=2)


class StandInVisits:
    """One stream per player. ``collisions`` saves fail first, each because
    ``beaten_by`` — another phone's close — landed a moment before."""

    def __init__(
        self, *, collisions: int = 0, beaten_by: NeedsYourAnswerClosed | None = None
    ) -> None:
        self.collisions = collisions
        self.beaten_by = beaten_by
        self.saved: list[NeedsYourAnswerVisit] = []
        self._streams: dict[UUID, list] = {}

    async def load(self, player_id: UUID) -> NeedsYourAnswerVisit:
        return NeedsYourAnswerVisit.from_history(
            player_id, self._streams.get(player_id, [])
        )

    async def save(self, visit: NeedsYourAnswerVisit) -> None:
        if self.collisions:
            self.collisions -= 1
            if self.beaten_by is not None:
                self._streams.setdefault(visit.player_id, []).append(self.beaten_by)
            raise EventStreamVersionConflict("another phone closed it first")
        self._streams.setdefault(visit.player_id, []).extend(visit.pull_events())
        self.saved.append(visit)


class StandInUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


def closing(visits: StandInVisits, uow: StandInUnitOfWork) -> CloseNeedsYourAnswer:
    return CloseNeedsYourAnswer(visits=visits, uow=uow, clock=MovableClock(NOW))


async def test_closing_records_the_watermark_and_commits_it():
    visits, uow = StandInVisits(), StandInUnitOfWork()
    player = uuid4()

    await closing(visits, uow).execute(player, watermark=MINE)

    assert (await visits.load(player)).watermark == MINE
    assert uow.commits == 1


async def test_closing_on_the_same_read_again_writes_nothing():
    visits, uow = StandInVisits(), StandInUnitOfWork()
    player = uuid4()
    await closing(visits, uow).execute(player, watermark=MINE)

    await closing(visits, uow).execute(player, watermark=MINE)

    assert len(visits.saved) == 1
    assert uow.commits == 1


async def test_a_close_with_no_watermark_records_nothing():
    """A read with nothing waiting serves none: the last answer closed the
    sheet, and nothing it showed is left to see."""

    visits, uow = StandInVisits(), StandInUnitOfWork()

    await closing(visits, uow).execute(uuid4(), watermark=None)

    assert (visits.saved, uow.commits, uow.rollbacks) == ([], 0, 0)


async def test_a_phone_beaten_by_an_older_close_closes_once_more_on_its_newer_read():
    player = uuid4()
    theirs = NeedsYourAnswerClosed(
        player_id=player, watermark=THEIRS, occurred_at=NOW - timedelta(seconds=1)
    )
    visits, uow = StandInVisits(collisions=1, beaten_by=theirs), StandInUnitOfWork()

    await closing(visits, uow).execute(player, watermark=MINE)

    assert (await visits.load(player)).watermark == MINE
    assert (uow.commits, uow.rollbacks) == (1, 1)


async def test_a_phone_beaten_by_a_newer_close_records_nothing():
    player = uuid4()
    theirs = NeedsYourAnswerClosed(
        player_id=player, watermark=NOW, occurred_at=NOW - timedelta(seconds=1)
    )
    visits, uow = StandInVisits(collisions=1, beaten_by=theirs), StandInUnitOfWork()

    await closing(visits, uow).execute(player, watermark=MINE)

    assert (await visits.load(player)).watermark == NOW
    assert (visits.saved, uow.commits, uow.rollbacks) == ([], 0, 1)


async def test_beaten_twice_it_gives_up_and_is_no_error():
    """Once more only: a third phone in the same instant is too much
    coincidence to chase, and its close stands."""

    visits, uow = StandInVisits(collisions=2), StandInUnitOfWork()

    await closing(visits, uow).execute(uuid4(), watermark=MINE)

    assert (visits.saved, uow.commits, uow.rollbacks) == ([], 0, 2)
