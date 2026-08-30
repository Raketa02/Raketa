"""*What have I been asked, and what have I asked for* — over the log.

Run against the real adapter and a real (SQLite) session, because the two things
worth asserting are exactly what a double would have to invent: the substring
match on the serialized seats that finds every challenge a player is seated in,
and the fold that decides whether they are still on that court.

Three claims:

**Newest first is part of the demand.** A list whose order depended on how the
streams happened to come back would reorder itself between two identical
requests, and the client renders them in order.

**The standing is derived at read.** A seat past its day reads as lapsed with no
sweep having run, so the list is right for the whole gap between a deadline and
anything noticing.

**A seat given to somebody else stops being yours.** The stream still matches the
substring read — their id is in an earlier event — and the challenge is not
theirs to keep watching.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.bootstrap.composition import (
    build_challenge_directory,
    build_challenge_repository,
    build_domain_event_store,
    build_event_publisher,
)
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.challenges.application.read_challenges import (
    ReadChallenges,
    ReadChallengesCommand,
)
from app.modules.challenges.domain.answer_window import ANSWER_WINDOW
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.origins import SentFromSearch
from app.modules.challenges.domain.seats import SeatPlan, Side
from app.modules.challenges.domain.standing import Standing
from app.modules.player_profile.domain.availability import Window
from app.shared.ids import new_uuid

ORGANISER = new_uuid()
ALICE = new_uuid()
BOB = new_uuid()
CAROL = new_uuid()
SEARCH = new_uuid()


def _from_search(position: int) -> SentFromSearch:
    return SentFromSearch(search_id=SEARCH, position=position)


def at(hours: int = 0) -> Instant:
    return instant(
        datetime(2026, 8, 30, 12, tzinfo=timezone.utc) + timedelta(hours=hours)
    )


class FrozenClock:
    def __init__(self, moment: Instant) -> None:
        self._at = moment

    def now(self) -> datetime:
        return self._at


def _repository(session):
    return build_challenge_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def _reading(session, *, now: Instant) -> ReadChallenges:
    return ReadChallenges(
        directory=build_challenge_directory(session), clock=FrozenClock(now)
    )


def a_tennis_challenge(*, invitee, sent_at: Instant) -> Challenge:
    return Challenge.sent(
        challenge_id=new_uuid(),
        sport=Sport.TENNIS,
        mode=SearchMode.FOR_FUN,
        window=Window.ANY,
        organiser_id=ORGANISER,
        arrangement=(
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(
                side=Side.B,
                player_id=invitee,
                origin=SentFromSearch(search_id=SEARCH, position=1),
            ),
        ),
        occurred_at=sent_at,
    )


async def _record(session, challenge: Challenge) -> Challenge:
    await _repository(session).save(challenge)
    await session.commit()
    return challenge


async def test_a_challenge_reaches_both_sides_of_it(session_factory):
    """*Challenge sent* and *Challenge for you* are one standing read from two
    sides, which is why nothing here takes a reader's point of view."""

    async with session_factory() as session:
        sent = await _record(session, a_tennis_challenge(invitee=ALICE, sent_at=at()))

        mine = await _reading(session, now=at(1)).execute(
            ReadChallengesCommand(reader_id=ORGANISER)
        )
        theirs = await _reading(session, now=at(1)).execute(
            ReadChallengesCommand(reader_id=ALICE)
        )

        assert [one.challenge.id for one in mine] == [sent.id]
        assert [one.challenge.id for one in theirs] == [sent.id]
        assert mine[0].standing is Standing.AWAITING_ANSWERS


async def test_a_stranger_sees_none_of_it(session_factory):
    async with session_factory() as session:
        await _record(session, a_tennis_challenge(invitee=ALICE, sent_at=at()))

        theirs = await _reading(session, now=at(1)).execute(
            ReadChallengesCommand(reader_id=BOB)
        )

        assert theirs == ()


async def test_the_list_is_newest_first(session_factory):
    """Ordered on ``opened_at``, so two identical requests cannot disagree."""

    async with session_factory() as session:
        first = await _record(session, a_tennis_challenge(invitee=ALICE, sent_at=at()))
        second = await _record(
            session, a_tennis_challenge(invitee=BOB, sent_at=at(2))
        )

        mine = await _reading(session, now=at(3)).execute(
            ReadChallengesCommand(reader_id=ORGANISER)
        )

        assert [one.challenge.id for one in mine] == [second.id, first.id]


async def test_the_standing_is_folded_against_the_clock_with_no_sweep_having_run(
    session_factory,
):
    """A seat past its day reads as lapsed whether or not anything has been past
    — the sweep exists for the record, not for correctness."""

    async with session_factory() as session:
        await _record(session, a_tennis_challenge(invitee=ALICE, sent_at=at()))

        inside = await _reading(session, now=at(1)).execute(
            ReadChallengesCommand(reader_id=ORGANISER)
        )
        outside = await _reading(
            session, now=instant(at() + ANSWER_WINDOW + timedelta(minutes=1))
        ).execute(ReadChallengesCommand(reader_id=ORGANISER))

        assert inside[0].standing is Standing.AWAITING_ANSWERS
        assert outside[0].standing is Standing.LAPSED


async def test_an_ended_challenge_stays_on_the_list(session_factory):
    """A list that quietly dropped this morning's decline would be the same class
    of lie as a read-back that got shorter."""

    async with session_factory() as session:
        challenge = a_tennis_challenge(invitee=ALICE, sent_at=at())
        challenge.decline(ALICE, occurred_at=at(1))
        await _record(session, challenge)

        theirs = await _reading(session, now=at(2)).execute(
            ReadChallengesCommand(reader_id=ALICE)
        )

        assert [one.standing for one in theirs] == [Standing.DECLINED]


async def test_a_seat_given_to_somebody_else_is_no_longer_yours(session_factory):
    """Their answer is still theirs and is what the aggregate remembers; the
    challenge is somebody else's now.

    A four rather than a singles court, because the seat has to be re-offered
    while the challenge still stands — and a singles challenge whose only invitee
    said no is over, with nobody left to keep faith with.
    """

    async with session_factory() as session:
        challenge = Challenge.sent(
            challenge_id=new_uuid(),
            sport=Sport.PADEL,
            mode=SearchMode.FOR_FUN,
            window=Window.WEEKEND,
            organiser_id=ORGANISER,
            arrangement=(
                SeatPlan(side=Side.A, player_id=ORGANISER),
                SeatPlan(side=Side.A, player_id=ALICE, origin=_from_search(1)),
                SeatPlan(side=Side.B, player_id=CAROL, origin=_from_search(2)),
                SeatPlan(side=Side.B),
            ),
            occurred_at=at(),
        )
        challenge.accept(CAROL, occurred_at=at(1))
        challenge.decline(ALICE, occurred_at=at(1))
        challenge.invite(
            (
                SeatPlan(side=Side.A, player_id=ORGANISER),
                SeatPlan(side=Side.A, player_id=BOB, origin=_from_search(3)),
                SeatPlan(side=Side.B, player_id=CAROL),
                SeatPlan(side=Side.B),
            ),
            occurred_at=at(2),
        )
        await _record(session, challenge)

        hers = await _reading(session, now=at(3)).execute(
            ReadChallengesCommand(reader_id=ALICE)
        )
        his = await _reading(session, now=at(3)).execute(
            ReadChallengesCommand(reader_id=BOB)
        )

        assert hers == ()
        assert [one.challenge.id for one in his] == [challenge.id]
