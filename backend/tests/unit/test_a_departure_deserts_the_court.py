"""``LeaveGame``'s hand-over, driven on stubs — what the departure tells ``games``,
and in which order (``docs/adr/0165`` §3).

The API suite proves the outcomes; this pins the **sentences** the use case hands
over, which no HTTP read can see: nothing at all for a court that was never a
game, the seat alone for a game that still has two on it, and the seat **then**
the call-off — ``called_by`` the leaver — for the departure that leaves one
player with nobody deciding, off the ending the aggregate recorded
(``docs/adr/0172`` §1). And the reply's ``game_id``: the game the court became,
asked of ``games`` for the redraw, and ``None`` where the fold says the court
was never one. Every collaborator is a hand-written stub implementing the
port, which is this suite's rule.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Collection, Mapping, Sequence
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.challenges.application.commands import LeaveGameCommand
from app.modules.challenges.application.leave_game import LeaveGame
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.origins import SentFromSearch
from app.modules.challenges.domain.seatable_game import LineUpChange
from app.modules.challenges.domain.seats import SeatPlan, Side
from app.modules.challenges.domain.standing import Standing
from app.modules.player_profile.domain.availability import Window
from app.shared.ids import new_uuid
from tests.unit.challenge_world import a_safe_court
from tests.unit.fake_event_store import CountingUnitOfWork, FrozenClock

ORGANISER, ALICE, BOB, CAROL = (new_uuid() for _ in range(4))
SEARCH = new_uuid()
SENT_AT = instant(datetime(2026, 9, 13, 12, tzinfo=timezone.utc))


def at(hours: int) -> Instant:
    return instant(SENT_AT + timedelta(hours=hours))


@dataclass
class _Challenges:
    held: dict[UUID, Challenge] = field(default_factory=dict)

    async def load(self, challenge_id: UUID) -> Challenge | None:
        return self.held.get(challenge_id)

    async def save(self, challenge: Challenge) -> None:
        challenge.pull_events()
        self.held[challenge.id] = challenge


class _Handles:
    async def names_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, str]:
        return {player_id: str(player_id)[:4] for player_id in player_ids}


class _SeatsMayChange:
    async def line_up_change_on(
        self, challenge_id: UUID, *, now: Instant
    ) -> LineUpChange:
        return LineUpChange.ADMITTED


@dataclass
class _Games:
    """The hand-over, remembering every sentence in the order it was told."""

    told: list[tuple[str, UUID]] = field(default_factory=list)

    async def open_planned_game(
        self,
        *,
        challenge_id: UUID,
        sport: Sport,
        counted: bool,
        window: str | None,
        line_up: Sequence[tuple[str, UUID]],
        occurred_at: Instant,
    ) -> UUID | None:
        self.told.append(("opened", challenge_id))
        return new_uuid()

    async def vacate_seat(
        self, *, challenge_id: UUID, player_id: UUID, occurred_at: Instant
    ) -> None:
        self.told.append(("vacated", player_id))

    async def call_off(
        self, *, challenge_id: UUID, by: UUID, occurred_at: Instant
    ) -> None:
        self.told.append(("called_off", by))


class _CourtGames:
    """*Which of these courts have a game* — every court asked about has one,
    and it is the same id every time it is asked."""

    def __init__(self) -> None:
        self.games: dict[UUID, UUID] = {}
        self.asked: list[frozenset[UUID]] = []

    async def games_of(self, challenge_ids: Collection[UUID]) -> Mapping[UUID, UUID]:
        self.asked.append(frozenset(challenge_ids))
        return {
            challenge_id: self.games.setdefault(challenge_id, new_uuid())
            for challenge_id in challenge_ids
        }


def _invited(player_id: UUID, side: Side, position: int) -> SeatPlan:
    return SeatPlan(
        side=side,
        player_id=player_id,
        origin=SentFromSearch(search_id=SEARCH, position=position),
    )


def _a_padel_four() -> Challenge:
    return Challenge.sent(
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        mode=SearchMode.FOR_FUN,
        window=Window.WEEKEND,
        organiser_id=ORGANISER,
        arrangement=(
            SeatPlan(side=Side.A, player_id=ORGANISER),
            _invited(ALICE, Side.A, 1),
            _invited(BOB, Side.B, 2),
            _invited(CAROL, Side.B, 3),
        ),
        occurred_at=SENT_AT,
    )


def _a_two() -> Challenge:
    return Challenge.sent(
        challenge_id=new_uuid(),
        sport=Sport.TENNIS,
        mode=SearchMode.COMPETITIVE,
        window=Window.TODAY,
        organiser_id=ORGANISER,
        arrangement=(
            SeatPlan(side=Side.A, player_id=ORGANISER),
            _invited(ALICE, Side.B, 1),
        ),
        occurred_at=SENT_AT,
    )


def _leave(
    challenge: Challenge,
    games: _Games,
    *,
    now: Instant,
    court_games: _CourtGames | None = None,
) -> LeaveGame:
    challenges = _Challenges()
    challenges.held[challenge.id] = challenge
    challenge.pull_events()
    return LeaveGame(
        challenges=challenges,
        names=_Handles(),
        safety=a_safe_court([ORGANISER, ALICE, BOB, CAROL]),
        games=_SeatsMayChange(),
        uow=CountingUnitOfWork(),
        clock=FrozenClock(now),
        planned_games=games,
        court_games=court_games or _CourtGames(),
    )


async def test_a_court_that_was_never_a_game_hands_nothing_over():
    """The fold already says what the departure did to it."""

    challenge = _a_padel_four()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.accept(BOB, occurred_at=at(2))
    games = _Games()

    court_games = _CourtGames()
    answered = await _leave(
        challenge, games, now=at(3), court_games=court_games
    ).execute(LeaveGameCommand(challenge_id=challenge.id, player_id=ALICE))

    assert games.told == []
    assert answered.standing is Standing.AWAITING_ANSWERS
    assert answered.game_id is None, "the fold's answer, not the other context's"
    assert court_games.asked == [frozenset()], "asked about no court, as the names are"


async def test_a_departure_that_leaves_two_on_a_game_opens_the_seat_and_no_more():
    challenge = _a_padel_four()
    for who in (ALICE, BOB, CAROL):
        challenge.accept(who, occurred_at=at(1))
    challenge.leave(CAROL, occurred_at=at(2))
    games = _Games()

    court_games = _CourtGames()
    answered = await _leave(
        challenge, games, now=at(3), court_games=court_games
    ).execute(LeaveGameCommand(challenge_id=challenge.id, player_id=BOB))

    assert games.told == [("vacated", BOB)]
    assert answered.standing is Standing.LINE_UP_INCOMPLETE
    assert answered.game_id == court_games.games[challenge.id]


async def test_the_departure_that_leaves_one_vacates_the_seat_and_then_calls_it_off():
    """The seat first, then the end, so the record reads in the order it
    happened — and ``called_by`` is the leaver, whose departure ended it. The
    court's own ending is the aggregate's, recorded beside the ``SeatLeft``,
    and the reply reads ``CALLED_OFF`` naming the leaver."""

    challenge = _a_padel_four()
    for who in (ALICE, BOB, CAROL):
        challenge.accept(who, occurred_at=at(1))
    challenge.leave(CAROL, occurred_at=at(2))
    challenge.leave(BOB, occurred_at=at(3))
    games = _Games()

    answered = await _leave(challenge, games, now=at(4)).execute(
        LeaveGameCommand(challenge_id=challenge.id, player_id=ALICE)
    )

    assert games.told == [("vacated", ALICE), ("called_off", ALICE)]
    assert answered.standing is Standing.CALLED_OFF, (
        "the court ends with its game (docs/adr/0172 §1)"
    )
    assert answered.ended_by == ALICE
    assert answered.game_id is not None


async def test_in_singles_either_player_leaving_calls_it_off():
    """Organiser-blind: the opponent's departure and the organiser's each leave
    one player on a two, and each calls the game off."""

    for leaver in (ALICE, ORGANISER):
        challenge = _a_two()
        challenge.accept(ALICE, occurred_at=at(1))
        games = _Games()

        await _leave(challenge, games, now=at(2)).execute(
            LeaveGameCommand(challenge_id=challenge.id, player_id=leaver)
        )

        assert games.told == [("vacated", leaver), ("called_off", leaver)]


async def test_a_seat_still_deciding_keeps_a_game_from_being_called_off():
    """Only the challenge can tell an open seat from one that is asked, which is
    why the rule is asked here and not of the game's line-up."""

    challenge = _a_padel_four()
    for who in (ALICE, BOB, CAROL):
        challenge.accept(who, occurred_at=at(1))
    challenge.leave(CAROL, occurred_at=at(2))
    challenge.leave(BOB, occurred_at=at(3))
    newcomer = new_uuid()
    challenge.invite(
        (
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(side=Side.A, player_id=ALICE),
            _invited(newcomer, Side.B, 4),
            SeatPlan(side=Side.B),
        ),
        by=ALICE,
        occurred_at=at(4),
    )
    games = _Games()

    await _leave(challenge, games, now=at(5)).execute(
        LeaveGameCommand(challenge_id=challenge.id, player_id=ALICE)
    )

    assert games.told == [("vacated", ALICE)]
