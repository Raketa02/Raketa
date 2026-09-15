"""Calling a game off — the fourth end, and the one an act reaches (``docs/adr/0163``).

**A game with a seat open can be called off**, and nothing else can. ``call_off``
writes ``GameCalledOff``; the standing reads it **first**, as ``challenges`` reads
its recorded conclusion; it is an end — settled, and refusing every act — and it
is **neither played nor a ghost**. Driven on the aggregate and on the use case
the call-off hands over to, with a hand-written repository, because what is
under test is *what the record does* rather than anything about a database.

**And the end says who, and its card can be cleared** (``docs/adr/0172`` §4–§5).
``called_off_by`` is folded off the event's ``called_by``, the field ADR-0163 §4
kept for this day; ``dismiss`` is the reader's own act on a called-off game,
recorded once per player and read by the rail alone.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.kernel import InvariantViolated, Sport, instant
from app.modules.games.application.call_off_game import CallOffGame
from app.modules.games.application.commands import (
    CallOffGameCommand,
    DismissGameCommand,
)
from app.modules.games.application.dismiss_game import DismissGame
from app.modules.games.domain.errors import (
    GameIsNotCalledOff,
    NotAGameToCallOff,
    TheGameIsNotOpenToSeating,
    TheGameWasCalledOff,
    TheResultIsSettled,
    YouWereNotOnThisCourt,
)
from app.modules.games.domain.events import GameCalledOff, GameDismissed
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.standing import PLAYED, SETTLED, GameStanding
from app.modules.games.domain.windows import ENTRY_GRACE, PLAN_HORIZON
from app.modules.player_profile.domain.availability import Window
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import CountingUnitOfWork, FrozenClock

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
    given to somebody else — a re-seat is a whole court, and the people who
    may act on it are the people on it."""

    game = _a_reopened_game()

    with pytest.raises(YouWereNotOnThisCourt):
        game.call_off(by=EVE, occurred_at=at(2))
    assert game.standing_at(at(2)) is GameStanding.AWAITING_ENTRY

    game.reseat(_four(ANA, BO, EVE, DEE), occurred_at=at(3))
    game.vacate(DEE, occurred_at=at(4))
    with pytest.raises(YouWereNotOnThisCourt):
        game.call_off(by=CY, occurred_at=at(5))


def test_somebody_whose_seat_is_the_open_one_may_call_it_off():
    """``docs/adr/0165`` §3 — the departure that leaves one player on a game
    calls it off, and ``called_by`` is the leaver, who has been vacated by then.
    **What the aggregate enforces is one step wider than that rule**: anybody
    whose leaving opened a seat that is still open, because the game cannot tell
    which departure emptied the court — an open seat and an asked one look the
    same here — and the narrower rule is the challenge's, which is the only
    caller. The record is honest about who, and the sentence the others read is
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
        game.reseat(_four(ANA, BO, EVE, DEE), occurred_at=at(3))
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


async def test_the_withdraw_hands_over_and_the_game_is_called_off():
    game = _a_reopened_game()
    games = _Remembering(game)

    await CallOffGame(games=games).execute(
        CallOffGameCommand(challenge_id=game.challenge_id, called_by=ANA),
        occurred_at=at(2),
    )

    assert game.standing_at(at(2)) is GameStanding.CALLED_OFF


async def test_a_game_that_has_already_ended_by_its_clock_is_stepped_over():
    """``docs/adr/0163`` §6 — a reopened court can outlive its game's window.
    The withdraw still ends the challenge, and the ghost stands as the end it
    already is rather than the act raising and holding the pair for ever."""

    ghost = _a_reopened_game()
    games = _Remembering(ghost)
    past_the_window = instant(
        PLANNED_AT + PLAN_HORIZON + ENTRY_GRACE + timedelta(hours=1)
    )

    await CallOffGame(games=games).execute(
        CallOffGameCommand(challenge_id=ghost.challenge_id, called_by=ANA),
        occurred_at=past_the_window,
    )

    assert ghost.standing_at(past_the_window) is GameStanding.NEVER_PLAYED
    assert ghost.called_off_at is None


async def test_a_game_already_called_off_is_not_reached_by_a_second_call_off():
    """``docs/adr/0172`` §1 — the departure that calls a game off now records
    the court's ending too, so the challenge is over and *Call it off* meets
    ``challenge_is_over`` before any hand-over. A second call-off reaching a
    game already called off is therefore a broken precondition rather than a
    state, and the aggregate's own refusal fires: the leniency here is one
    standing wide, the ghost's, and no wider."""

    game = _a_reopened_game()
    game.call_off(by=CY, occurred_at=at(2))
    games = _Remembering(game)

    with pytest.raises(NotAGameToCallOff):
        await CallOffGame(games=games).execute(
            CallOffGameCommand(challenge_id=game.challenge_id, called_by=ANA),
            occurred_at=at(3),
        )
    assert game.called_off_at == at(2), "the first end stands"
    assert game.called_off_by == CY


async def test_only_the_ghost_is_stepped_over():
    """The leniency is one standing wide and no wider: a played game has a
    whole court, and a whole court is a challenge that is ``ON``, which the
    call-off refuses — so a played game here is a broken precondition, and the
    aggregate's refusal fires and rolls the act back."""

    game = _a_game()
    game.state_result(by=ANA, score=_score(), occurred_at=at(1))
    games = _Remembering(game)

    with pytest.raises(NotAGameToCallOff):
        await CallOffGame(games=games).execute(
            CallOffGameCommand(challenge_id=game.challenge_id, called_by=BO),
            occurred_at=at(3),
        )


async def test_a_call_off_for_a_challenge_with_no_game_is_a_broken_precondition():
    with pytest.raises(InvariantViolated):
        await CallOffGame(games=_Remembering()).execute(
            CallOffGameCommand(challenge_id=new_uuid(), called_by=ANA),
            occurred_at=at(1),
        )


# ---------------------------------------------------------------------------
# The dismissal — a per-player act, derived on every read (ADR-0172 §5)
# ---------------------------------------------------------------------------


def test_a_player_on_the_court_dismisses_a_called_off_game_once():
    """Recorded once per player on the game's stream; a second dismissal by
    the same player writes nothing and answers as done, on *writes nothing
    twice*. Nothing about the game's standing moves."""

    game = _a_reopened_game()
    game.call_off(by=ANA, occurred_at=at(2))
    game.pull_events()

    game.dismiss(by=BO, occurred_at=at(3))
    game.dismiss(by=BO, occurred_at=at(4))
    game.dismiss(by=ANA, occurred_at=at(5))

    events = game.pull_events()
    assert [type(event) for event in events] == [GameDismissed, GameDismissed]
    assert [(event.dismissed_by, event.occurred_at) for event in events] == [
        (BO, at(3)),
        (ANA, at(5)),
    ]
    assert game.dismissed == {BO, ANA}
    assert game.standing_at(at(6)) is GameStanding.CALLED_OFF
    assert Game.from_history(
        [*_a_reopened_game_events(), *events]
    ).dismissed == {BO, ANA}


def _a_reopened_game_events():
    game = _a_reopened_game()
    game.call_off(by=ANA, occurred_at=at(2))
    return game.pull_events()


def test_a_dismissal_is_admitted_on_a_called_off_game_and_on_no_other_standing():
    """Refused with its own code on every other standing — awaiting its
    entry, a ghost, played and argued, confirmed — because the other endings'
    cards carry a score or a strand's verdict and are the record for the day
    they stay; this one carries nothing the row does not."""

    awaiting = _a_reopened_game()
    with pytest.raises(GameIsNotCalledOff):
        awaiting.dismiss(by=ANA, occurred_at=at(2))

    ghost = _a_reopened_game()
    past_the_window = instant(
        PLANNED_AT + PLAN_HORIZON + ENTRY_GRACE + timedelta(hours=1)
    )
    with pytest.raises(GameIsNotCalledOff):
        ghost.dismiss(by=ANA, occurred_at=past_the_window)

    played = _a_game()
    played.state_result(by=ANA, score=_score(), occurred_at=at(1))
    with pytest.raises(GameIsNotCalledOff):
        played.dismiss(by=CY, occurred_at=at(2))
    with pytest.raises(GameIsNotCalledOff):
        played.dismiss(by=CY, occurred_at=at(24 * 8))
    assert played.dismissed == frozenset()


def test_only_somebody_on_the_court_may_dismiss_and_the_leaver_is_not():
    """Admitted for a player the rail would show the card to — on the court —
    and answered as a stranger is answered for anybody else. The leaver whose
    departure called it off has been vacated: the card is not on their rail,
    and neither is the act theirs."""

    game = _a_reopened_game()
    game.call_off(by=CY, occurred_at=at(2))

    with pytest.raises(YouWereNotOnThisCourt):
        game.dismiss(by=EVE, occurred_at=at(3))
    with pytest.raises(YouWereNotOnThisCourt):
        game.dismiss(by=CY, occurred_at=at(3))
    game.dismiss(by=ANA, occurred_at=at(3))
    assert game.dismissed == {ANA}


async def test_the_use_case_records_the_dismissal_and_a_stranger_is_refused():
    game = _a_reopened_game()
    game.call_off(by=ANA, occurred_at=at(2))
    games = _Remembering(game)
    uow = CountingUnitOfWork()

    def dismiss(hours: int) -> DismissGame:
        return DismissGame(games=games, uow=uow, clock=FrozenClock(at(hours)))

    await dismiss(3).execute(DismissGameCommand(game_id=game.id, player_id=BO))
    await dismiss(4).execute(DismissGameCommand(game_id=game.id, player_id=BO))

    assert game.dismissed == {BO}
    assert game.version == 4, "one dismissal appended, the second wrote nothing"
    assert uow.commits == 2, "answered as done both times"
    with pytest.raises(YouWereNotOnThisCourt):
        await dismiss(5).execute(DismissGameCommand(game_id=game.id, player_id=EVE))
    with pytest.raises(YouWereNotOnThisCourt):
        await dismiss(5).execute(
            DismissGameCommand(game_id=new_uuid(), player_id=BO)
        )
