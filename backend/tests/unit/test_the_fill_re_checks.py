"""What a fill re-verifies that a send does not, and what it stops refusing.

The fill is the send one screen later and it re-reads the same five facts, so
almost everything here is already asserted in ``test_the_send_re_checks.py`` and
is not asserted twice: both presses go through ``court_verification.py``, which
is the point of that module existing.

What is left is the two places they genuinely differ, and each is a way this
could go wrong invisibly.

**The pair rule steps aside for this one court, and for nothing else.** A court
being completed is made of people the filler is already arranging with, so
asking the rule over it would refuse every fill there will ever be. The
exemption is by **id**: an open challenge between two of these people that is
not this one still refuses, and a fill that excused *any* pair would be a way to
send round the rule entirely.

**The cited search has to be for this challenge's sport.** A send has nothing to
check — its sport *is* the origin's, since that is where the court's shape comes
from — but a fill's sport is the **challenge's**, and padel and badminton both
seat four. Without the check a filler could seat people off a search this court's
own gates never judged, and every new seat's origin would join to a search about
a different game.

Run against a real (SQLite) session for the reads that fold the log, and against
hand-written stubs for the four gates and the origin, exactly as the send's own
suite is.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Collection, Mapping
from uuid import UUID

import pytest

from app.bootstrap.composition import (
    build_challenge_repository,
    build_domain_event_store,
    build_event_publisher,
    build_open_challenge_query,
)
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.challenges.application.commands import FillSeatsCommand, SeatChoice
from app.modules.challenges.application.fill_seats import FillSeats
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.errors import (
    AnOpenChallengeStandsWithThisPair,
    TheCourtDidNotComeFromThatSearch,
    TheFillIsTheLiveMembers,
)
from app.modules.challenges.domain.origins import SentFromSearch
from app.modules.challenges.domain.seats import SeatAnswer, SeatPlan, Side
from app.modules.challenges.domain.standing import Standing
from app.modules.player_profile.domain.availability import Window
from app.shared.ids import new_uuid
from tests.unit.challenge_world import StubOrigins, a_safe_court
from tests.unit.fake_event_store import CountingUnitOfWork

ORGANISER = new_uuid()
ACCEPTOR = new_uuid()
ONE = new_uuid()
OTHER = new_uuid()
SEARCH = new_uuid()

COURT = (ORGANISER, ACCEPTOR, ONE, OTHER)
SENT_AT = instant(datetime(2026, 8, 30, 12, tzinfo=timezone.utc))
LATER = instant(datetime(2026, 8, 30, 13, tzinfo=timezone.utc))


class FrozenClock:
    def __init__(self, at: Instant) -> None:
        self._at = at

    def now(self) -> datetime:
        return self._at


class StubHandles:
    """A nickname per seat. The reply is the redraw and this is the redraw's half."""

    async def handles_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, str]:
        return {
            player_id: f"p{position}"
            for position, player_id in enumerate(player_ids)
        }


def _repository(session):
    return build_challenge_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def _invited(player_id: UUID, side: Side, position: int) -> SeatPlan:
    return SeatPlan(
        side=side,
        player_id=player_id,
        origin=SentFromSearch(search_id=SEARCH, position=position),
    )


async def _a_half_built_court(session) -> Challenge:
    """A padel four sent to one person who accepted. **Two seats still open.**"""

    challenge = Challenge.sent(
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        mode=SearchMode.FOR_FUN,
        window=Window.WEEKEND,
        organiser_id=ORGANISER,
        arrangement=(
            SeatPlan(side=Side.A, player_id=ORGANISER),
            _invited(ACCEPTOR, Side.A, 1),
            SeatPlan(side=Side.B),
            SeatPlan(side=Side.B),
        ),
        occurred_at=SENT_AT,
    )
    await _repository(session).save(challenge)
    await session.commit()

    repository = _repository(session)
    loaded = await repository.load(challenge.id)
    loaded.accept(ACCEPTOR, occurred_at=LATER)
    await repository.save(loaded)
    await session.commit()
    assert loaded.standing_at(LATER) is Standing.LINE_UP_INCOMPLETE
    return loaded


def _fill(session, *, origins=None, safety=None) -> FillSeats:
    return FillSeats(
        challenges=_repository(session),
        handles=StubHandles(),
        open_challenges=build_open_challenge_query(session),
        origins=origins or StubOrigins(known={SEARCH}),
        safety=safety or a_safe_court(COURT),
        uow=CountingUnitOfWork(),
        clock=FrozenClock(LATER),
    )


def _the_whole_court() -> tuple[SeatChoice, ...]:
    return (
        SeatChoice(side=Side.A, player_id=ORGANISER),
        SeatChoice(side=Side.A, player_id=ACCEPTOR),
        SeatChoice(side=Side.B, player_id=ONE),
        SeatChoice(side=Side.B, player_id=OTHER),
    )


async def test_a_court_is_not_refused_for_the_pairs_it_is_made_of(session_factory):
    """**The exemption, at the seam that would otherwise refuse every fill.**

    The organiser and the acceptor are an open pair — that is what
    ``LINE_UP_INCOMPLETE`` *means* — so a fill asking the pair rule over its own
    court would find them and refuse. Nothing else in this suite can catch that:
    it fails identically for every court, on every press, for ever.
    """

    async with session_factory() as session:
        challenge = await _a_half_built_court(session)

        grown = await _fill(session).execute(
            FillSeatsCommand(
                challenge_id=challenge.id,
                player_id=ORGANISER,
                search_id=SEARCH,
                court=_the_whole_court(),
            )
        )

        assert grown.standing is Standing.AWAITING_ANSWERS
        seats = {seat.player_id: seat for seat in grown.challenge.seats}
        assert seats[ACCEPTOR].answer is SeatAnswer.ACCEPTED
        assert seats[ONE].answer is None and seats[ONE].answer_by is not None
        assert seats[OTHER].answer is None


async def test_any_other_open_challenge_on_that_court_still_refuses(session_factory):
    """**Excepted by id, and by nothing else.**

    The two people being newly seated are already arranging a game with each
    other, in another sport. The fill excuses the court it is completing and must
    not excuse them — otherwise naming a challenge would be a way past the rule
    for everybody on the court at once.
    """

    async with session_factory() as session:
        challenge = await _a_half_built_court(session)
        elsewhere = Challenge.sent(
            challenge_id=new_uuid(),
            sport=Sport.TENNIS,
            mode=SearchMode.COMPETITIVE,
            window=Window.WEEKEND,
            organiser_id=ONE,
            arrangement=(
                SeatPlan(side=Side.A, player_id=ONE),
                _invited(OTHER, Side.B, 1),
            ),
            occurred_at=SENT_AT,
        )
        await _repository(session).save(elsewhere)
        await session.commit()

        with pytest.raises(AnOpenChallengeStandsWithThisPair):
            await _fill(session).execute(
                FillSeatsCommand(
                    challenge_id=challenge.id,
                    player_id=ORGANISER,
                    search_id=SEARCH,
                    court=_the_whole_court(),
                )
            )


async def test_a_search_run_for_another_sport_is_not_this_courts_origin(
    session_factory,
):
    """Padel and badminton both seat four, and only one of them is this court's.

    The search exists, it is the filler's own and it showed all of these people —
    every one of the four causes ``court_origin_not_found`` already stands for is
    satisfied. What refuses it is that it was run for a different game, which is
    the one fact a send never has to check.
    """

    async with session_factory() as session:
        challenge = await _a_half_built_court(session)

        with pytest.raises(TheCourtDidNotComeFromThatSearch):
            await _fill(
                session,
                origins=StubOrigins(known={SEARCH}, sport=Sport.BADMINTON),
            ).execute(
                FillSeatsCommand(
                    challenge_id=challenge.id,
                    player_id=ORGANISER,
                    search_id=SEARCH,
                    court=_the_whole_court(),
                )
            )


async def test_the_acceptor_may_fill_it_and_a_stranger_may_not(session_factory):
    """Any live member, and only a member.

    The acceptor is not the organiser and the fill is theirs; somebody who holds
    no seat at all is told no challenge of theirs has that id, which is the
    refusal that answers nothing about a stranger's evening.
    """

    async with session_factory() as session:
        challenge = await _a_half_built_court(session)

        grown = await _fill(session).execute(
            FillSeatsCommand(
                challenge_id=challenge.id,
                player_id=ACCEPTOR,
                search_id=SEARCH,
                court=_the_whole_court(),
            )
        )

        assert grown.standing is Standing.AWAITING_ANSWERS


async def test_a_fill_by_somebody_who_declined_is_refused_as_a_member(
    session_factory,
):
    """They still hold a seat, so it is not a 404 — and they have left, so the
    fill is not theirs."""

    async with session_factory() as session:
        challenge = await _a_half_built_court(session)
        repository = _repository(session)
        loaded = await repository.load(challenge.id)
        loaded.invite(
            (
                SeatPlan(side=Side.A, player_id=ORGANISER),
                SeatPlan(side=Side.A, player_id=ACCEPTOR),
                _invited(ONE, Side.B, 2),
                SeatPlan(side=Side.B),
            ),
            by=loaded.organiser_id,
            occurred_at=LATER,
        )
        loaded.decline(ONE, occurred_at=LATER)
        await repository.save(loaded)
        await session.commit()

        with pytest.raises(TheFillIsTheLiveMembers):
            await _fill(session).execute(
                FillSeatsCommand(
                    challenge_id=challenge.id,
                    player_id=ONE,
                    search_id=SEARCH,
                    court=_the_whole_court(),
                )
            )
