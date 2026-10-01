"""Which courts a card may be drawn for — **all six standings, pinned.**

``RATEABLE`` is ``SETTLED & PLAYED``, derived from ``games``' own two sets so a
new ending added over there arrives here as a question rather than as a silent
omission — which is exactly what happened when ``CALLED_OFF`` arrived
(``docs/adr/0163``): the sweep below went red on the missing builder, and the
answer was the derivation's. Derivation makes it right; it does not make it
*asserted*, and ``docs/adr/0158`` §7 calls two of the members load-bearing by
name:

**A ghost is out, and so is a called-off game.** ``NEVER_PLAYED`` and
``CALLED_OFF`` are settled over in ``games`` and there is nobody to rate for an
evening that did not happen — so the intersection is the whole of the narrowing,
and a reader who reached for ``SETTLED`` alone would offer cards for games nobody
turned up to.

**An unscored game is in, on purpose.** Two people who cannot agree what the
score was were still on a court together for two hours, and how that went is
exactly what this context exists to collect. It is the member somebody
simplifying to *confirmed* would drop, and nothing else in the suite would
notice: every game the HTTP test settles is confirmed.

The file also pins the other half of the port's contract — that a game the caller
did not play in is not findable through it at all, because the read asks *which
games are mine* rather than *which game is this*.

**Both arities are swept over the same six standings**, because they are one
question and the narrowing has one home: a list that offered a ghost and a
singular that refused one would be a screen showing a card the act behind it
would not accept.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.kernel import Instant, Sport, instant
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.standing import GameStanding
from app.modules.games.domain.windows import (
    ENTRY_GRACE,
    PLAN_HORIZON,
    PROPOSAL_WINDOW,
)
from app.modules.sportsmanship.infrastructure.games_settled_courts import (
    RATEABLE,
    GamesSettledCourts,
)
from app.shared.ids import new_uuid

PLANNED_AT = instant(datetime(2026, 9, 1, 18, 0, tzinfo=timezone.utc))
A_SCORE = Score.of([SetScore(a=6, b=4), SetScore(a=6, b=3)])


@dataclass
class Directory:
    """``GameDirectory`` over a list, answering only about people on the court.

    The real one finds streams by matching the serialized court, so a game the
    caller did not play in is invisible to it. Stubbing that faithfully is the
    point of this class: a stub that answered with everything would let the test
    pass while the port leaked other people's evenings.
    """

    games: tuple[Game, ...] = ()

    async def playing(self, player_id: UUID) -> tuple[Game, ...]:
        return tuple(
            game for game in self.games if player_id in game.line_up.players
        )


def a_doubles_game(*players: UUID) -> Game:
    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=None,
        line_up=LineUp.of(
            Seating(
                side=GameSide.A if seat < 2 else GameSide.B,
                player_id=player_id,
            )
            for seat, player_id in enumerate(players)
        ),
        occurred_at=PLANNED_AT,
    )


def _four() -> tuple[UUID, UUID, UUID, UUID]:
    return (new_uuid(), new_uuid(), new_uuid(), new_uuid())


#: One builder per standing, each returning the game and the instant to read it
#: at. Written as data so the parametrised test below is exhaustive over
#: ``GameStanding`` by construction rather than by somebody remembering.
def _awaiting_entry():
    game = a_doubles_game(*_four())
    return game, instant(PLANNED_AT + timedelta(days=1))


def _never_played():
    game = a_doubles_game(*_four())
    return game, instant(PLANNED_AT + PLAN_HORIZON + ENTRY_GRACE + timedelta(hours=1))


def _called_off():
    """Somebody left, and somebody still on the court called it off."""

    players = _four()
    game = a_doubles_game(*players)
    game.vacate(players[3], occurred_at=instant(PLANNED_AT + timedelta(hours=1)))
    called = instant(PLANNED_AT + timedelta(hours=2))
    game.call_off(by=players[0], occurred_at=called)
    return game, instant(called + timedelta(hours=1))


def _started_short():
    """A booked game somebody left, whose hour came with the seat still open
    (#544)."""

    players = _four()
    starts = instant(PLANNED_AT + timedelta(days=3))
    game = Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=None,
        line_up=a_doubles_game(*players).line_up,
        occurred_at=PLANNED_AT,
        starts_at=starts,
    )
    game.vacate(players[3], occurred_at=instant(starts - timedelta(hours=2)))
    return game, instant(starts + timedelta(hours=1))


def _awaiting_answer():
    players = _four()
    game = a_doubles_game(*players)
    entered = instant(PLANNED_AT + timedelta(days=1))
    game.state_result(by=players[0], score=A_SCORE, occurred_at=entered)
    return game, instant(entered + timedelta(hours=1))


def _confirmed():
    players = _four()
    game = a_doubles_game(*players)
    entered = instant(PLANNED_AT + timedelta(days=1))
    game.state_result(by=players[0], score=A_SCORE, occurred_at=entered)
    return game, instant(entered + PROPOSAL_WINDOW + timedelta(minutes=1))


def _unscored():
    """Both sides put a score up, neither gave way, and both windows closed."""

    players = _four()
    game = a_doubles_game(*players)
    entered = instant(PLANNED_AT + timedelta(days=1))
    game.state_result(by=players[0], score=A_SCORE, occurred_at=entered)
    countered = instant(entered + timedelta(hours=2))
    game.state_result(
        by=players[2],
        score=Score.of([SetScore(a=4, b=6), SetScore(a=3, b=6)]),
        occurred_at=countered,
    )
    return game, instant(countered + PROPOSAL_WINDOW + timedelta(minutes=1))


BUILDERS = {
    GameStanding.AWAITING_ENTRY: _awaiting_entry,
    GameStanding.NEVER_PLAYED: _never_played,
    GameStanding.CALLED_OFF: _called_off,
    GameStanding.AWAITING_ANSWER: _awaiting_answer,
    GameStanding.CONFIRMED: _confirmed,
    GameStanding.UNSCORED: _unscored,
    GameStanding.STARTED_SHORT: _started_short,
}

#: The two the card may be drawn for. Spelled out rather than derived, so this
#: file disagrees with ``RATEABLE`` if somebody changes the derivation — which is
#: the only way a test of a derived constant is worth writing.
MAY_BE_RATED = {GameStanding.CONFIRMED, GameStanding.UNSCORED}


def test_every_standing_has_a_builder():
    """The guard on the guard: a table missing a standing would make the sweep
    below silently narrower than the enum it claims to be exhaustive over."""

    assert set(BUILDERS) == set(GameStanding)


@pytest.mark.parametrize("standing", sorted(GameStanding, key=lambda one: one.value))
async def test_a_card_may_be_drawn_for_exactly_the_two_endings_that_happened(
    standing: GameStanding,
):
    game, read_at = BUILDERS[standing]()
    assert game.standing_at(read_at) is standing, "the fixture built the wrong state"

    (me, *_rest) = sorted(game.line_up.players)
    courts = GamesSettledCourts(Directory(games=(game,)))
    court = await courts.court_of(game.id, player_id=me, now=read_at)

    if standing in MAY_BE_RATED:
        assert court is not None, f"{standing.value} should be rateable"
        assert court.game_id == game.id
        assert court.rater_id == me
        assert set(court.others) == game.line_up.players - {me}
        assert court.played_at == game.played_at
    else:
        assert court is None, f"{standing.value} should not be rateable"


@pytest.mark.parametrize("standing", sorted(GameStanding, key=lambda one: one.value))
async def test_the_list_offers_exactly_the_same_two_endings(standing: GameStanding):
    """**One narrowing, two arities.** A list that offered an ending the act
    refuses would draw a card nothing could answer."""

    game, read_at = BUILDERS[standing]()
    (me, *_rest) = sorted(game.line_up.players)
    courts = GamesSettledCourts(Directory(games=(game,)))

    found = await courts.courts_of(me, now=read_at)

    if standing in MAY_BE_RATED:
        (only,) = found
        assert only.game_id == game.id
        assert only.rater_id == me
        assert set(only.others) == game.line_up.players - {me}
        assert only.played_at == game.played_at
    else:
        assert found == ()


async def test_the_list_carries_every_settled_court_of_theirs():
    """**The whole record, not a page of it.** The card's week is applied by the
    use case over what this answers, so a port that stopped at the first would
    hide a card somebody still has time to answer."""

    players = _four()
    mine = tuple(_confirmed_for(players)[0] for _ in range(3))
    read_at = _confirmed_for(players)[1]
    somebody_elses, _ = _confirmed()
    courts = GamesSettledCourts(Directory(games=mine + (somebody_elses,)))

    found = await courts.courts_of(players[0], now=read_at)

    assert {one.game_id for one in found} == {game.id for game in mine}


async def test_a_player_on_nobodys_court_has_no_list_at_all():
    game, read_at = _confirmed()
    courts = GamesSettledCourts(Directory(games=(game,)))

    assert await courts.courts_of(new_uuid(), now=read_at) == ()


def test_the_two_that_may_be_rated_are_the_ones_the_constant_names():
    assert RATEABLE == MAY_BE_RATED


async def test_a_court_offers_everybody_else_in_the_line_ups_own_order():
    """Not a set. A walk over a court is the same walk on every process and
    under every ``PYTHONHASHSEED`` (``docs/adr/0105``)."""

    players = _four()
    game, read_at = _confirmed_for(players)
    courts = GamesSettledCourts(Directory(games=(game,)))

    court = await courts.court_of(game.id, player_id=players[1], now=read_at)

    assert court is not None
    assert court.others == (players[0], players[2], players[3])


async def test_a_game_the_caller_did_not_play_in_is_not_findable_at_all():
    """*You may only rate a court you were on* is the shape of the query rather
    than a check somebody remembered to write."""

    game, read_at = _confirmed()
    courts = GamesSettledCourts(Directory(games=(game,)))

    assert await courts.court_of(game.id, player_id=new_uuid(), now=read_at) is None


async def test_an_unknown_game_is_the_same_absence():
    game, read_at = _confirmed()
    (me, *_rest) = sorted(game.line_up.players)
    courts = GamesSettledCourts(Directory(games=(game,)))

    assert await courts.court_of(new_uuid(), player_id=me, now=read_at) is None


def _confirmed_for(players: tuple[UUID, ...]) -> tuple[Game, Instant]:
    game = a_doubles_game(*players)
    entered = instant(PLANNED_AT + timedelta(days=1))
    game.state_result(by=players[0], score=A_SCORE, occurred_at=entered)
    return game, instant(entered + PROPOSAL_WINDOW + timedelta(minutes=1))
