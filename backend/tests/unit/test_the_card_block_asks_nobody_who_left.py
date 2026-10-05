"""**Nobody who has left is asked about — the reader included** (``docs/adr/0143``
§8, amended by [#392](https://github.com/Raketa02/Raketa/issues/392)).

§8 states the rule for the people *on* the court and states why it is enforced by
**not putting them in the question**: so that there is *no card computed, no
photograph signed and nothing to leak*. The departed **reader** was owed the same
and was not getting it ([#394](https://github.com/Raketa02/Raketa/issues/394)) —
they reached the read, because a departed seat is still their seat and they need
the row, and the court was then assembled in their direction over everybody still
on it.

**So these assert the enforcement style rather than the response.** A test that
checked the answer carried no cards would pass over an implementation that
computed every one of them, signed a photograph URL each and filtered late. What
is asserted is that ``cards_for`` is **never reached**, which is the only shape
under which there is nothing to leak.

The clock is here rather than over HTTP for one case that cannot be reached
otherwise: a seat whose day ran out with **no sweep having been past** still reads
as gone, and the guard is ``is_live_at`` precisely so that it does — an
implementation testing ``answer in (DECLINED, LAPSED)`` passes every other test in
this file and hands that reader the whole court.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Collection, Mapping, Sequence
from uuid import UUID

import pytest

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.challenges.application.read_challenge import (
    ReadChallenge,
    ReadChallengeCommand,
)
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.errors import NoChallengeOfYoursHasThatId
from app.modules.challenges.domain.origins import SentFromSearch
from app.modules.challenges.domain.ports import CourtCards, CourtSeat
from app.modules.challenges.domain.seats import SeatPlan, Side
from app.modules.challenges.domain.standing import Standing
from app.modules.player_profile.domain.weekly_hours import Window
from app.shared.ids import new_uuid

ORGANISER = new_uuid()
ACCEPTED = new_uuid()
DEPARTED = new_uuid()
SILENT = new_uuid()
SEARCH = new_uuid()


def at(hours: int = 0) -> Instant:
    return instant(
        datetime(2026, 9, 1, 12, tzinfo=timezone.utc) + timedelta(hours=hours)
    )


class _Repository:
    """The one challenge under test, and a `save` nothing here reaches."""

    def __init__(self, challenge: Challenge) -> None:
        self._challenge = challenge

    async def load(self, challenge_id: UUID) -> Challenge | None:
        return self._challenge if challenge_id == self._challenge.id else None

    async def save(self, challenge: Challenge) -> None:  # pragma: no cover
        raise AssertionError("a read may not write")


class _Handles:
    async def names_of(self, player_ids: Sequence[UUID]) -> Mapping[UUID, str]:
        return {player_id: f"h{n}" for n, player_id in enumerate(player_ids)}


class _Pairings:
    """A spy. **Whether it was called at all is the assertion.**"""

    def __init__(self) -> None:
        self.asked_about: list[frozenset[UUID]] = []

    async def cards_for(
        self,
        *,
        reader_id: UUID,
        sport: Sport,
        mode: SearchMode | None,
        court: Collection[CourtSeat],
    ) -> CourtCards:
        self.asked_about.append(frozenset(seat.player_id for seat in court))
        return CourtCards()


class _Clock:
    def __init__(self, now: Instant) -> None:
        self._now = now

    def now(self) -> Instant:
        return self._now


def a_court_still_being_filled(*, silent_seat: bool = False) -> Challenge:
    """A padel four in a live standing, with one person who has left it.

    ``ORGANISER`` proposes and is accepted from birth, ``ACCEPTED`` is in, and
    ``DEPARTED`` has gone. The fourth seat is either empty — which leaves the
    court ``LINE_UP_INCOMPLETE`` — or held by somebody still deciding, which makes
    it ``AWAITING_ANSWERS``: the two live standings, and the rule has to be the
    same in both.
    """

    fourth = (
        SeatPlan(
            side=Side.B,
            player_id=SILENT,
            origin=SentFromSearch(search_id=SEARCH, position=3),
        )
        if silent_seat
        else SeatPlan(side=Side.B)
    )
    challenge = Challenge.sent(
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        mode=SearchMode.FOR_FUN,
        window=Window.WEEKEND,
        organiser_id=ORGANISER,
        arrangement=(
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(
                side=Side.A,
                player_id=ACCEPTED,
                origin=SentFromSearch(search_id=SEARCH, position=1),
            ),
            SeatPlan(
                side=Side.B,
                player_id=DEPARTED,
                origin=SentFromSearch(search_id=SEARCH, position=2),
            ),
            fourth,
        ),
        occurred_at=at(0),
    )
    challenge.accept(ACCEPTED, occurred_at=at(1))
    return challenge


def a_read_of(challenge: Challenge, *, now: Instant) -> tuple[ReadChallenge, _Pairings]:
    pairings = _Pairings()
    return (
        ReadChallenge(
            challenges=_Repository(challenge),
            names=_Handles(),
            pairings=pairings,
            clock=_Clock(now),
        ),
        pairings,
    )


async def _read(challenge: Challenge, *, by: UUID, now: Instant):
    read, pairings = a_read_of(challenge, now=now)
    answer = await read.execute(
        ReadChallengeCommand(challenge_id=challenge.id, reader_id=by)
    )
    return answer, pairings


# ---------------------------------------------------------------------------
# The reader who has left
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("silent_seat", [False, True])
async def test_a_reader_who_declined_is_asked_about_nobody(silent_seat: bool):
    """**In both live standings**, which is the pair this bug was drawn two ways.

    ``standing_of`` holds ``AWAITING_ANSWERS`` while *any* seat is awaiting, so a
    padel four sits there with this reader's answer already given — and that is
    the arm the client was drawing a card block on.
    """

    challenge = a_court_still_being_filled(silent_seat=silent_seat)
    challenge.decline(DEPARTED, occurred_at=at(2))

    answer, pairings = await _read(challenge, by=DEPARTED, now=at(3))

    assert answer.standing is (
        Standing.AWAITING_ANSWERS if silent_seat else Standing.LINE_UP_INCOMPLETE
    )
    assert pairings.asked_about == []
    assert answer.court is None
    assert answer.card_for(ACCEPTED) is None
    assert answer.card_for(ORGANISER) is None


async def test_a_reader_whose_day_ran_out_unswept_is_asked_about_nobody():
    """**The case no sweep has been past**, and the reason the guard is
    ``is_live_at`` rather than a test of the recorded answer.

    Their seat still says nothing at all — ``answer`` is ``None`` — and it has
    read as gone since the deadline passed. An implementation keyed on
    ``DECLINED`` or ``LAPSED`` hands this reader the whole court.
    """

    challenge = a_court_still_being_filled()
    seat = challenge.seat_of(DEPARTED)
    assert seat is not None and seat.answer is None

    past_their_day = instant(seat.answer_by + timedelta(minutes=1))
    answer, pairings = await _read(challenge, by=DEPARTED, now=past_their_day)

    assert answer.standing is Standing.LINE_UP_INCOMPLETE
    assert pairings.asked_about == []
    assert answer.court is None


async def test_the_departed_reader_keeps_the_whole_arrangement_and_every_handle():
    """**Only the card goes.** §13's sentences for a departed reader quote nobody,
    but the arrangement and the names are what keep the row readable — and
    ``docs/adr/0143`` §8 keeps the handle on exactly this argument."""

    challenge = a_court_still_being_filled()
    challenge.decline(DEPARTED, occurred_at=at(2))

    answer, _ = await _read(challenge, by=DEPARTED, now=at(3))

    assert len(answer.challenge.seats) == 4
    assert answer.names.keys() == {ORGANISER, ACCEPTED, DEPARTED}
    assert answer.read_at == at(3)


# ---------------------------------------------------------------------------
# The readers who are still in it
# ---------------------------------------------------------------------------


async def test_a_reader_who_accepted_is_still_asked_about_everybody_still_in():
    """**The case the two reasons for this rule disagree about** (#392).

    They have no answer left to give either — but they are still on the court and
    the pair still holds them, so the predicate is *has this reader left* and
    never *has this reader answered*.
    """

    challenge = a_court_still_being_filled()
    challenge.decline(DEPARTED, occurred_at=at(2))

    answer, pairings = await _read(challenge, by=ACCEPTED, now=at(3))

    assert pairings.asked_about == [frozenset({ORGANISER})]
    assert answer.court is not None


async def test_the_organiser_is_asked_about_everybody_still_in():
    """Their seat is accepted from birth, so it is live for the life of the
    challenge and this guard never touches them."""

    challenge = a_court_still_being_filled()
    challenge.decline(DEPARTED, occurred_at=at(2))

    answer, pairings = await _read(challenge, by=ORGANISER, now=at(3))

    assert pairings.asked_about == [frozenset({ACCEPTED})]
    assert answer.court is not None


# ---------------------------------------------------------------------------
# The rules this one sits beside
# ---------------------------------------------------------------------------


async def test_an_ended_challenge_asks_about_nobody_whoever_reads_it():
    """The rule that was already there, as the control: the card block belongs to
    an arrangement being decided, and it stops when the deciding does.

    The ending here is the organiser removing the court once the one who had
    joined left it (``docs/adr/0165`` §4), with the fourth seat still deciding —
    so the reader whose day is still running is drawn no card either, and no
    card is computed for a court that is over.
    """

    challenge = a_court_still_being_filled(silent_seat=True)
    challenge.decline(DEPARTED, occurred_at=at(2))
    challenge.leave(ACCEPTED, occurred_at=at(3))
    challenge.withdraw(ORGANISER, occurred_at=at(4))

    for reader in (ORGANISER, ACCEPTED, DEPARTED, SILENT):
        answer, pairings = await _read(challenge, by=reader, now=at(5))

        assert answer.standing is Standing.WITHDRAWN
        assert pairings.asked_about == []
        assert answer.court is None


async def test_somebody_with_no_seat_is_told_the_challenge_does_not_exist():
    """The departed reader is admitted by seat ownership alone and **must be** —
    they need the row. A stranger is not, and the two refusals are one code."""

    challenge = a_court_still_being_filled()
    read, pairings = a_read_of(challenge, now=at(3))

    with pytest.raises(NoChallengeOfYoursHasThatId):
        await read.execute(
            ReadChallengeCommand(challenge_id=challenge.id, reader_id=new_uuid())
        )

    assert pairings.asked_about == []
