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

**And a fourth, from ``docs/adr/0143`` §7:** the names come back with the rows,
read once over the union of every court, and a seat whose account ``users`` no
longer has keeps its place with no handle on it.
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
from app.modules.player_profile.domain.weekly_hours import Window
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


class RecordingHandles:
    """What ``users`` calls these people — and what it was asked about.

    A stub rather than the real adapter, because the claim worth making is about
    the **question**: one set read over the union of every court, so a player
    seated in three of your challenges is asked about once. Whether ``users``
    can answer is ``users``'s own suite's.
    """

    def __init__(self, known: dict | None = None) -> None:
        self.known = {} if known is None else known
        self.asked: list[tuple] = []

    async def names_of(self, player_ids):
        self.asked.append(tuple(player_ids))
        return {
            player_id: self.known[player_id]
            for player_id in player_ids
            if player_id in self.known
        }


class NoCourtHasAGame:
    """``GameOfCourtQuery`` for courts none of which has completed: the fold
    never asks about one, and this answers nobody if it did — and nobody has
    cleared what was never a game."""

    async def games_of(self, challenge_ids):
        return {}

    async def dismissed_of(self, challenge_ids, *, by):
        return frozenset()


def _reading(
    session, *, now: Instant, names: RecordingHandles | None = None
) -> ReadChallenges:
    return ReadChallenges(
        directory=build_challenge_directory(session),
        names=names or RecordingHandles(),
        court_games=NoCourtHasAGame(),
        clock=FrozenClock(now),
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

        _, mine = await _reading(session, now=at(1)).execute(
            ReadChallengesCommand(reader_id=ORGANISER)
        )
        _, theirs = await _reading(session, now=at(1)).execute(
            ReadChallengesCommand(reader_id=ALICE)
        )

        assert [one.challenge.id for one in mine] == [sent.id]
        assert [one.challenge.id for one in theirs] == [sent.id]
        assert mine[0].standing is Standing.AWAITING_ANSWERS


async def test_a_stranger_sees_none_of_it(session_factory):
    async with session_factory() as session:
        await _record(session, a_tennis_challenge(invitee=ALICE, sent_at=at()))

        _, theirs = await _reading(session, now=at(1)).execute(
            ReadChallengesCommand(reader_id=BOB)
        )

        assert theirs == ()


async def test_the_list_is_newest_first(session_factory):
    """Ordered on ``opened_at``, so two identical requests cannot disagree."""

    async with session_factory() as session:
        first = await _record(session, a_tennis_challenge(invitee=ALICE, sent_at=at()))
        second = await _record(session, a_tennis_challenge(invitee=BOB, sent_at=at(2)))

        _, mine = await _reading(session, now=at(3)).execute(
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

        _, inside = await _reading(session, now=at(1)).execute(
            ReadChallengesCommand(reader_id=ORGANISER)
        )
        _, outside = await _reading(
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

        _, theirs = await _reading(session, now=at(2)).execute(
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
            by=challenge.organiser_id,
            occurred_at=at(2),
        )
        await _record(session, challenge)

        _, hers = await _reading(session, now=at(3)).execute(
            ReadChallengesCommand(reader_id=ALICE)
        )
        _, his = await _reading(session, now=at(3)).execute(
            ReadChallengesCommand(reader_id=BOB)
        )

        assert hers == ()
        assert [one.challenge.id for one in his] == [challenge.id]


# ---------------------------------------------------------------------------
# The names, and the instant — ``docs/adr/0143`` §7
# ---------------------------------------------------------------------------


async def test_the_handles_are_one_question_over_the_union_of_every_court(
    session_factory,
):
    """One set read for the whole list, and a player seated twice asked about once.

    The union rather than a question per court, and **sorted**, because a set is
    never the source of a traversal (``docs/adr/0105`` §1) — nothing downstream
    could observe the order, which is exactly why the rule is stated on the
    collection rather than on what happens to be visible.
    """

    names = RecordingHandles({ORGANISER: "Ola", ALICE: "Alicja", BOB: "Bartek"})
    async with session_factory() as session:
        await _record(session, a_tennis_challenge(invitee=ALICE, sent_at=at()))
        await _record(session, a_tennis_challenge(invitee=BOB, sent_at=at(1)))

        _, mine = await _reading(session, now=at(2), names=names).execute(
            ReadChallengesCommand(reader_id=ORGANISER)
        )

        assert names.asked == [tuple(sorted([ORGANISER, ALICE, BOB]))]
        assert all(
            one.names == {ORGANISER: "Ola", ALICE: "Alicja", BOB: "Bartek"}
            for one in mine
        )


async def test_a_seat_whose_account_is_gone_keeps_its_place_with_no_handle(
    session_factory,
):
    """**A player absent from the answer keeps their seat.**

    A card with no name is not a card and a shortlist drops that row; a
    *seat* with no name is still a person who was asked, and dropping it
    would publish a court one person short. The handle goes absent, the seat
    stays, and the screen has a side to name instead.
    """

    names = RecordingHandles({ORGANISER: "Ola"})
    async with session_factory() as session:
        await _record(session, a_tennis_challenge(invitee=ALICE, sent_at=at()))

        _, mine = await _reading(session, now=at(1), names=names).execute(
            ReadChallengesCommand(reader_id=ORGANISER)
        )

        assert len(mine[0].challenge.seats) == 2
        assert mine[0].names == {ORGANISER: "Ola"}


async def test_the_instant_answers_even_when_the_list_is_empty(session_factory):
    """The fold's own moment, beside the rows as well as on them.

    An empty list still has to say **when**: a client's countdowns are read
    against it and there would otherwise be no row to read it off.
    """

    async with session_factory() as session:
        read_at, mine = await _reading(session, now=at(4)).execute(
            ReadChallengesCommand(reader_id=BOB)
        )

        assert mine == ()
        assert read_at == at(4)


async def test_every_standing_is_folded_against_the_one_instant(session_factory):
    """One clock read for the whole list, carried on every row.

    Folding each challenge against its own reading would let a list disagree
    with itself about which of two seats had just lapsed.
    """

    async with session_factory() as session:
        await _record(session, a_tennis_challenge(invitee=ALICE, sent_at=at()))
        await _record(session, a_tennis_challenge(invitee=BOB, sent_at=at(1)))

        read_at, mine = await _reading(session, now=at(2)).execute(
            ReadChallengesCommand(reader_id=ORGANISER)
        )

        assert {one.read_at for one in mine} == {read_at}
