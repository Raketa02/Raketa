"""Leaving standby: the write that asks nothing, and what Now is told after it.

ADR-0087's seventh act, driven through hand-written stubs, so everything here is
about the *rules* and nothing about a database — the table is
`tests/unit/test_standby_places.py`'s and the route is `tests/api/test_standby.py`'s.

Four claims carry the file:

1. **Nothing is checked before the write.** *Deleting a standby place the viewer
   does not hold returns what a success returns* is the acceptance criterion,
   and the way to satisfy it is to have no membership gate at all: anybody may
   queue for any match, so there is nobody to be a stranger to. The only 404 is
   an address that names no match.
2. **The card goes with the place.** A queue place is the whole of what put that
   match on her strip, so leaving produces ADR-0070's *this card is gone* — the
   first thing in the product that can.
3. **Unless she is something else to it.** A leaver or a seat holder who also
   carried a queue place keeps her card, recomposed, and the queue place she has
   just dropped is the one thing about it that changed.
4. **The read happens after the commit**, so the answer describes the record as
   it stands rather than as the write left it in memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.kernel import Cover, Instant, grosze
from app.modules.matches.domain.errors import MatchNotFound
from app.modules.now.application.standby import LeaveStandby, LeaveStandbyCommand
from app.modules.now.domain.enrolled import Enrolment
from app.modules.now.domain.screen import CardChanged, CardGone, Money, Place

from tests.unit.fake_event_store import CountingUnitOfWork
from tests.unit.match_records import a_match, at

WARSAW = ZoneInfo("Europe/Warsaw")
SHARE = grosze(3800)
COURT = grosze(15200)
VIEWER = UUID("11111111-1111-1111-1111-111111111111")
MATCH = UUID("33333333-3333-3333-3333-333333333333")
NOW: Instant = at(-2000)


@dataclass
class _Clock:
    at: datetime

    def now(self) -> datetime:
        return self.at


class StubEnrolled:
    """The membership read, answering whatever the case left behind the write.

    It takes the row it will answer with **after** the delete, because that is
    the only read this use case makes: the answer is composed from what is true
    once the place is gone.
    """

    def __init__(self, row: Enrolment | None) -> None:
        self.row = row
        self.asked: list[tuple[UUID, UUID]] = []

    async def for_player(self, *, player_id: UUID, now: Instant):
        raise AssertionError("leaving standby never reads the whole strip")

    async def one(
        self, *, player_id: UUID, match_id: UUID, now: Instant
    ) -> Enrolment | None:
        self.asked.append((player_id, match_id))
        return self.row


class StubStandby:
    """The write, which either deletes or refuses the address."""

    def __init__(self, *, raises: Exception | None = None) -> None:
        self._raises = raises
        self.calls: list[tuple[UUID, UUID]] = []

    async def leave(self, *, match_id: UUID, player_id: UUID) -> None:
        self.calls.append((match_id, player_id))
        if self._raises is not None:
            raise self._raises


def a_place(**kwargs) -> Place:
    return Place(
        **{
            "club_id": uuid4(),
            "club_name": "Sport Club Krakow",
            "zone": WARSAW,
            "cover": Cover.INDOOR,
            **kwargs,
        }
    )


def enrolled(record=None, **kwargs) -> Enrolment:
    return Enrolment(
        **{
            "match_id": MATCH,
            "record": record if record is not None else a_match(paid=2),
            "where": a_place(),
            "share": Money(amount=SHARE),
            "court_total": Money(amount=COURT),
            **kwargs,
        }
    )


def make(
    *,
    row: Enrolment | None = None,
    standby: StubStandby | None = None,
) -> tuple[LeaveStandby, StubEnrolled, StubStandby, CountingUnitOfWork]:
    read = StubEnrolled(row)
    write = standby or StubStandby()
    uow = CountingUnitOfWork()
    use_case = LeaveStandby(
        enrolled=read, standby=write, uow=uow, clock=_Clock(NOW)
    )
    return use_case, read, write, uow


def a_command(**kwargs) -> LeaveStandbyCommand:
    return LeaveStandbyCommand(
        **{"player_id": VIEWER, "match_id": MATCH, **kwargs}
    )


# --- the write ------------------------------------------------------------


async def test_the_place_is_deleted_for_this_viewer_and_this_match() -> None:
    use_case, _, write, _ = make()

    await use_case.execute(a_command())

    assert write.calls == [(MATCH, VIEWER)]


async def test_the_write_commits() -> None:
    """The delete and the read that composes the answer close together."""

    use_case, _, _, uow = make()

    await use_case.execute(a_command())

    assert uow.commits == 1


async def test_nothing_is_read_before_the_write() -> None:
    """The acceptance criterion, stated from the side that produces it.

    *Deleting a standby place the viewer does not hold returns what a success
    returns* is satisfied by having no membership gate: a pre-read would have to
    answer *is she queued*, and the only thing it could do with a `no` is refuse
    — which is the second shape ADR-0070 forbids. The single read happens after
    the commit, so it can only be composing the answer.
    """

    use_case, read, write, _ = make()

    await use_case.execute(a_command())

    assert len(read.asked) == 1
    assert write.calls, "the write ran"


async def test_leaving_a_queue_she_is_not_on_answers_what_a_success_answers() -> None:
    """Two taps, the second on a place that is already gone, one shape."""

    use_case, _, _, _ = make()

    first = await use_case.execute(a_command())
    second = await use_case.execute(a_command())

    assert isinstance(first, CardGone)
    assert first == second


async def test_a_match_that_does_not_exist_is_the_only_refusal() -> None:
    """And it is about the **address**, not about the act.

    Anybody may queue for any match, so there is no membership to be a stranger
    to — which is what makes this the only thing that can go wrong.
    """

    use_case, _, _, uow = make(standby=StubStandby(raises=MatchNotFound()))

    with pytest.raises(MatchNotFound):
        await use_case.execute(a_command())

    assert uow.commits == 0


# --- what Now is told -----------------------------------------------------


async def test_a_viewer_who_was_only_queued_is_told_the_card_is_gone() -> None:
    """ADR-0070's *this card is no longer on your screen*, first produced here.

    A queue place is the whole of what put that match on her strip, so nothing
    survives the delete for a card to describe.
    """

    use_case, _, _, _ = make(row=None)

    update = await use_case.execute(a_command())

    assert update == CardGone(match_id=MATCH)


async def test_the_gone_form_names_the_match_and_carries_no_card() -> None:
    """Because there is none: she is nothing to the match now.

    An emptied card would be an answer to *what is this match doing* composed
    for somebody who is not asking, and the client would then have to decide
    what an empty card means.
    """

    use_case, _, _, _ = make(row=None)

    update = await use_case.execute(a_command())

    assert [field for field in vars(update)] == ["match_id", "update_type"]


async def test_a_seat_holder_keeps_her_card_recomposed() -> None:
    """The queue place and the seat are two memberships, and only one went.

    Nothing refuses a player holding both — the ladder already answers it, since
    rung 7 tests *not seated* — so the card that comes back is her seat's.
    """

    use_case, _, _, _ = make(row=enrolled(holds_seat=True))

    update = await use_case.execute(a_command())

    assert isinstance(update, CardChanged)
    assert update.card.match_id == MATCH


async def test_the_card_that_comes_back_no_longer_names_the_act() -> None:
    """Which is the correction she can *see*, rather than one she is told.

    The row the answer is composed from is read after the commit, so it carries
    `on_standby=False` — and the act is composed off the situation, so the
    button goes with the place.
    """

    use_case, _, _, _ = make(row=enrolled(holds_seat=True, on_standby=False))

    update = await use_case.execute(a_command())

    assert isinstance(update, CardChanged)
    assert update.card.act is None


async def test_a_leaver_who_also_queued_keeps_her_card() -> None:
    """ADR-0030 keeps a leaver's card until her outcome settles.

    She is still something to the match after the queue place goes, so the
    *gone* form would be dropping the one card that tells her whether her seat
    refills.
    """

    use_case, _, _, _ = make(row=enrolled(holds_seat=False))

    update = await use_case.execute(a_command())

    assert isinstance(update, CardChanged)


async def test_the_answer_is_read_after_the_commit(monkeypatch) -> None:
    """So it describes the record as it stands rather than as the write left it.

    Asserted by order rather than by value, because the two are the same value
    in a stub — and the failure this exists for is a composed answer that
    contradicts the row a second reader would find.
    """

    order: list[str] = []
    use_case, read, write, uow = make(row=None)

    original_leave = write.leave
    original_commit = uow.commit
    original_one = read.one

    async def leave(**kwargs):
        order.append("leave")
        return await original_leave(**kwargs)

    async def commit():
        order.append("commit")
        return await original_commit()

    async def one(**kwargs):
        order.append("read")
        return await original_one(**kwargs)

    monkeypatch.setattr(write, "leave", leave)
    monkeypatch.setattr(uow, "commit", commit)
    monkeypatch.setattr(read, "one", one)

    await use_case.execute(a_command())

    assert order == ["leave", "commit", "read"]


async def test_the_answer_is_asked_about_this_viewer_and_this_match() -> None:
    """A card composed for somebody else is the one thing worse than none."""

    use_case, read, _, _ = make(row=enrolled(holds_seat=True))

    await use_case.execute(a_command())

    assert read.asked == [(VIEWER, MATCH)]
