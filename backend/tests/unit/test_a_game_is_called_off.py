"""Calling a game off — the fourth end, and the one an act reaches (``docs/adr/0163``).

**A game with a seat open can be called off**, and nothing else can. ``call_off``
writes ``GameCalledOff``; the standing reads it **first**; it is an end —
settled, and refusing every act — and it is **neither played nor a ghost**.
Driven on the aggregate and on the use case the call-off hands over to, with a
hand-written repository, because what is under test is *what the record does*
rather than anything about a database.

**And the end says who** (``docs/adr/0172`` §4): ``called_off_by`` is folded
off the event's ``called_by``, the field ADR-0163 §4 kept for this day. A
booking's cut-off names nobody (#544).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.kernel import InvariantViolated, Sport, instant
from app.modules.games.application.call_off_game import CallOffGame
from app.modules.games.application.commands import CallOffGameCommand
from app.modules.games.domain.errors import (
    NotAGameToCallOff,
    TheCourtHasAnOpenSeat,
    TheGameIsNotOpenToSeating,
    TheGameWasCalledOff,
    TheResultIsSettled,
    YouWereNotOnThisCourt,
)
from app.modules.games.domain.events import GameCalledOff
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.standing import PLAYED, SETTLED, GameStanding
from app.modules.games.domain.windows import ENTRY_GRACE, PLAN_HORIZON
from app.modules.player_profile.domain.weekly_hours import Window
from app.shared.ids import new_uuid

ANA, BO, CY, DEE, EVE = (new_uuid() for _ in range(5))
PLANNED_AT = instant(datetime(2026, 9, 12, 18, 0, tzinfo=timezone.utc))


def at(hours: int) -> datetime:
    return instant(PLANNED_AT + timedelta(hours=hours))


def _four(a=ANA, b=BO, c=CY, d=DEE) -> LineUp:
    return LineUp.of(
        (
            Seating(side=GameSide.A, player_id=a),
            Seating(side=GameSide.A, player_id=b),
            Seating(side=GameSide.B, player_id=c),
            Seating(side=GameSide.B, player_id=d),
        )
    )


def _a_game(line_up: LineUp | None = None) -> Game:
    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=Window.WEEKEND,
        line_up=line_up or _four(),
        occurred_at=PLANNED_AT,
    )


def _a_reopened_game() -> Game:
    game = _a_game()
    game.vacate(CY, occurred_at=at(1))
    return game


def test_a_court_with_a_seat_open_takes_no_score():
    """``docs/adr/0162`` §3: a score on a court with a seat open is a score
    with a side nobody can price. A booked game meets its hour first — before
    it no score is taken, and at it the game started short (#654, #544) — so
    this is the refusal of a game with no hour."""

    game = _a_reopened_game()

    with pytest.raises(TheCourtHasAnOpenSeat):
        game.state_result(
            by=ANA,
            score=Score.of((SetScore(a=6, b=4), SetScore(a=6, b=3))),
            occurred_at=at(2),
        )
    assert game.standing_at(at(2)) is GameStanding.AWAITING_ENTRY


#: A booked game's hour, three days after it was booked.
HOUR = at(72)


def _a_booked_game_short_of_one() -> Game:
    """A booked game somebody left (#544): a seat open, its hour ahead."""

    game = Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=None,
        line_up=_four(),
        occurred_at=PLANNED_AT,
        starts_at=HOUR,
    )
    game.vacate(CY, occurred_at=at(1))
    return game


def _score() -> Score:
    return Score.of((SetScore(a=6, b=3), SetScore(a=6, b=4)))


# ---------------------------------------------------------------------------
# The fourth end
# ---------------------------------------------------------------------------


def test_a_game_with_a_seat_open_is_called_off_and_that_is_its_end():
    game = _a_reopened_game()

    game.call_off(by=ANA, occurred_at=at(2))

    assert game.called_off_at == at(2)
    assert game.called_off_by == ANA, "the field ADR-0163 §4 kept for this day"
    assert game.standing_at(at(2)) is GameStanding.CALLED_OFF
    assert game.standing_at(at(24 * 365)) is GameStanding.CALLED_OFF, (
        "a decision, not a deadline: a year of clock moves nothing"
    )
    event = game.pull_events()[-1]
    assert isinstance(event, GameCalledOff)
    assert (event.game_id, event.called_by, event.occurred_at) == (game.id, ANA, at(2))


def test_called_off_is_read_before_the_clock_as_withdrawn_is_read_before_the_seats():
    """The entry window closing after the act changes nothing: the standing was
    decided by a person, and the fold asks about that first."""

    game = _a_reopened_game()
    game.call_off(by=ANA, occurred_at=at(2))
    past_the_window = instant(
        PLANNED_AT + PLAN_HORIZON + ENTRY_GRACE + timedelta(hours=1)
    )

    assert game.standing_at(past_the_window) is GameStanding.CALLED_OFF
    assert game.was_played_at(past_the_window) is False


def test_called_off_is_settled_and_not_played():
    assert GameStanding.CALLED_OFF in SETTLED
    assert GameStanding.CALLED_OFF not in PLAYED


def test_the_whole_life_replays_into_itself():
    game = _a_reopened_game()
    game.call_off(by=BO, occurred_at=at(2))
    events = game.pull_events()

    rebuilt = Game.from_history(events)

    assert rebuilt.called_off_at == at(2)
    assert rebuilt.called_off_by == BO
    assert rebuilt.standing_at(at(3)) is GameStanding.CALLED_OFF
    assert rebuilt.version == 3
    assert not rebuilt.line_up.is_complete, "the open seat is still on the record"


def test_a_game_that_was_not_called_off_names_nobody():
    game = _a_reopened_game()
    assert game.called_off_by is None

    ghost = _a_reopened_game()
    past_the_window = instant(
        PLANNED_AT + PLAN_HORIZON + ENTRY_GRACE + timedelta(hours=1)
    )
    assert ghost.standing_at(past_the_window) is GameStanding.NEVER_PLAYED
    assert ghost.called_off_by is None


# ---------------------------------------------------------------------------
# What it refuses
# ---------------------------------------------------------------------------


def test_only_a_court_with_a_seat_open_can_be_called_off():
    """A full court that will not play lets its window lapse into *Never
    played*, as today (#411 rule 4)."""

    whole = _a_game()

    with pytest.raises(NotAGameToCallOff):
        whole.call_off(by=ANA, occurred_at=at(1))
    assert whole.standing_at(at(1)) is GameStanding.AWAITING_ENTRY


def test_a_game_that_has_ended_by_its_clock_cannot_be_called_off():
    """A ghost stays a ghost: a call-off that reached it would flip a standing
    the platform has already drawn, and un-charge a strand after the fact."""

    ghost = _a_reopened_game()
    past_the_window = instant(
        PLANNED_AT + PLAN_HORIZON + ENTRY_GRACE + timedelta(hours=1)
    )
    assert ghost.standing_at(past_the_window) is GameStanding.NEVER_PLAYED

    with pytest.raises(NotAGameToCallOff):
        ghost.call_off(by=ANA, occurred_at=past_the_window)
    assert ghost.standing_at(past_the_window) is GameStanding.NEVER_PLAYED


def test_a_game_already_called_off_cannot_be_called_off_again():
    game = _a_reopened_game()
    game.call_off(by=ANA, occurred_at=at(2))

    with pytest.raises(NotAGameToCallOff):
        game.call_off(by=BO, occurred_at=at(3))


def test_only_somebody_on_the_court_can_call_it_off():
    """A stranger cannot, and neither can somebody whose seat has since been
    given to somebody else — a rescue that makes the court whole leaves
    nobody's departure on it, and the people who may act on it are the
    people on it."""

    game = _a_reopened_game()

    with pytest.raises(YouWereNotOnThisCourt):
        game.call_off(by=EVE, occurred_at=at(2))
    assert game.standing_at(at(2)) is GameStanding.AWAITING_ENTRY

    game.take_seat(EVE, side=GameSide.B, occurred_at=at(3))
    game.vacate(DEE, occurred_at=at(4))
    with pytest.raises(YouWereNotOnThisCourt):
        game.call_off(by=CY, occurred_at=at(5))


def test_somebody_whose_seat_is_the_open_one_may_call_it_off():
    """``docs/adr/0165`` §3 — the departure that leaves one player on a game
    calls it off, and ``called_by`` is the leaver, who has been vacated by then.
    **What the aggregate enforces is one step wider than that rule**: anybody
    whose leaving opened a seat that is still open, because the game cannot tell
    which departure emptied the court — an open seat and an asked one look the
    same here — and the narrower rule was the challenge's, its caller until
    #578. The record is honest about who, and the sentence the others read is
    the client's to word."""

    game = _a_reopened_game()

    game.call_off(by=CY, occurred_at=at(2))

    assert game.standing_at(at(2)) is GameStanding.CALLED_OFF
    event = game.pull_events()[-1]
    assert isinstance(event, GameCalledOff) and event.called_by == CY


def test_a_called_off_game_refuses_every_act():
    """The entry names the end it met, with its own code, as a ghost's entry
    does; the acceptance meets the umbrella, as it does on a ghost; and nothing
    on the line-up moves."""

    game = _a_reopened_game()
    game.call_off(by=ANA, occurred_at=at(2))

    with pytest.raises(TheGameWasCalledOff):
        game.state_result(by=ANA, score=_score(), occurred_at=at(3))
    with pytest.raises(TheResultIsSettled):
        game.accept_result(by=DEE, occurred_at=at(3))
    with pytest.raises(TheGameIsNotOpenToSeating):
        game.vacate(ANA, occurred_at=at(3))
    with pytest.raises(TheGameIsNotOpenToSeating):
        game.take_seat(EVE, side=GameSide.B, occurred_at=at(3))
    assert game.outcome_for(ANA, now=at(3)) is None
    assert game.confirmed_score_at(at(3)) is None


# ---------------------------------------------------------------------------
# The hand-over
# ---------------------------------------------------------------------------


class _Remembering:
    def __init__(self, *games: Game) -> None:
        self.games: dict[UUID, Game] = {}
        for game in games:
            game.pull_events()
            self.games[game.id] = game

    async def load(self, game_id: UUID) -> Game | None:
        return self.games.get(game_id)

    async def for_challenge(self, challenge_id: UUID) -> Game | None:
        for game in self.games.values():
            if game.challenge_id == challenge_id:
                return game
        return None

    async def save(self, game: Game) -> None:
        game.pull_events()
        self.games[game.id] = game


async def test_the_cut_off_hands_over_and_the_game_is_called_off_by_nobody():
    game = _a_booked_game_short_of_one()
    games = _Remembering(game)

    await CallOffGame(games=games).execute(
        CallOffGameCommand(challenge_id=game.challenge_id, called_by=None),
        occurred_at=at(2),
    )

    assert game.standing_at(at(2)) is GameStanding.CALLED_OFF
    assert game.called_off_by is None


async def test_a_game_that_started_short_is_stepped_over():
    """#544 — a booking's cut-off call-off can arrive after its hour, by which
    time the game short of a player has *started short*. The act is about the
    booking, and the game keeps the end it already reached."""

    game = _a_booked_game_short_of_one()
    games = _Remembering(game)
    after_the_hour = instant(HOUR + timedelta(minutes=5))

    await CallOffGame(games=games).execute(
        CallOffGameCommand(challenge_id=game.challenge_id, called_by=None),
        occurred_at=after_the_hour,
    )

    assert game.standing_at(after_the_hour) is GameStanding.STARTED_SHORT
    assert game.called_off_at is None


async def test_a_game_already_called_off_is_not_reached_by_a_second_call_off():
    """A second call-off reaching a game already called off is a broken
    precondition rather than a state, and the aggregate's own refusal fires:
    the leniency here is one standing wide, *started short*, and no wider."""

    game = _a_booked_game_short_of_one()
    game.call_off(by=None, occurred_at=at(2))
    games = _Remembering(game)

    with pytest.raises(NotAGameToCallOff):
        await CallOffGame(games=games).execute(
            CallOffGameCommand(challenge_id=game.challenge_id, called_by=None),
            occurred_at=at(3),
        )
    assert game.called_off_at == at(2), "the first end stands"


async def test_a_ghost_is_no_longer_stepped_over():
    """The step-over a reopened challenge court needed (``docs/adr/0163`` §6)
    went with the challenges (#578): nothing calls off a game whose entry
    window has closed, so one arriving is a broken precondition and the
    aggregate's refusal fires and rolls the act back."""

    ghost = _a_reopened_game()
    games = _Remembering(ghost)
    past_the_window = instant(
        PLANNED_AT + PLAN_HORIZON + ENTRY_GRACE + timedelta(hours=1)
    )

    with pytest.raises(NotAGameToCallOff):
        await CallOffGame(games=games).execute(
            CallOffGameCommand(challenge_id=ghost.challenge_id, called_by=None),
            occurred_at=past_the_window,
        )
    assert ghost.called_off_at is None


async def test_a_played_game_is_not_stepped_over():
    game = _a_game()
    game.state_result(by=ANA, score=_score(), occurred_at=at(1))
    games = _Remembering(game)

    with pytest.raises(NotAGameToCallOff):
        await CallOffGame(games=games).execute(
            CallOffGameCommand(challenge_id=game.challenge_id, called_by=None),
            occurred_at=at(3),
        )


async def test_a_call_off_for_a_booking_with_no_game_is_a_broken_precondition():
    with pytest.raises(InvariantViolated):
        await CallOffGame(games=_Remembering()).execute(
            CallOffGameCommand(challenge_id=new_uuid(), called_by=None),
            occurred_at=at(1),
        )


# ---------------------------------------------------------------------------
# When a game became history — one moment, dated once
# ---------------------------------------------------------------------------


def test_a_game_became_history_at_the_entry_the_window_or_the_call_off():
    """``GAME_IS_HISTORY`` has one date, and every reader of it reads this.

    The seat change refuses on the standing, the deck's cool-off and the
    pairwise record run from the moment — so the moment is folded on the
    aggregate, once. Three endings: the entry that said *we played* whatever
    the score does afterwards, the window closing on a plan nobody claimed,
    and the call-off, dated from nothing but itself.
    """

    played = _a_game()
    played.state_result(by=ANA, score=_score(), occurred_at=at(2))
    assert played.became_history_at(at(3)) == at(2)
    # Whatever happens to the score afterwards, the game went behind them at
    # the entry: a proposal window closing does not re-date the evening.
    assert played.became_history_at(at(48)) == at(2)

    ghost = _a_game()
    window_closes = instant(PLANNED_AT + PLAN_HORIZON + ENTRY_GRACE)
    assert ghost.became_history_at(instant(window_closes + timedelta(hours=1))) == (
        window_closes
    )

    called_off = _a_reopened_game()
    called_off.call_off(by=ANA, occurred_at=at(2))
    assert called_off.became_history_at(at(3)) == at(2)


def test_a_game_awaiting_its_entry_is_not_history_whatever_its_moment_says():
    """``None`` while the game is ahead — a plan whose agreed moment has passed
    can still be moved, so the seat change's ``MOMENT_PASSED`` is a different
    answer from this one and is not folded here."""

    game = _a_game()
    assert game.became_history_at(at(1)) is None
    assert game.became_history_at(instant(PLANNED_AT + PLAN_HORIZON)) is None
    assert game.standing_at(at(1)) is GameStanding.AWAITING_ENTRY
