"""The pairing read's Social vibe (#835), against stub ports: **asked only on a
friendly with every seat filled, and read on its own ground.**

The vibe and the pairing are two reads over one request's transaction. On
Postgres a failed statement aborts that transaction, so whichever read fails
first costs every read after it — the stubs here share one ``Transaction``
that behaves so. Two things follow, and each is held below:

- **the tags are read before the Levels**, so a Levels read that fails (and the
  pairing port swallows, as it does) never costs the vibe;
- **a tags read that fails costs the vibe and nothing else it can spare**: it
  is logged and drawn as no vibe, the posture the pairing port holds for its
  own reads (``docs/adr/0161`` §4), never a refused screen.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.kernel import Sport, instant
from app.modules.games.application.read_game_pairing import ReadGamePairing
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.ports import Pairing
from app.modules.player_profile.domain.social_tags import SocialTag
from app.shared.ids import new_uuid
from tests.unit.fake_clock import MovableClock

NOW = datetime(2026, 10, 5, 6, tzinfo=timezone.utc)
OLA, ANIA, MAREK, ZOFIA = (new_uuid() for _ in range(4))
DRINK = SocialTag.STAYS_FOR_A_DRINK


class Transaction:
    """A request's one transaction: aborted by the first statement that fails,
    and every statement after it fails too."""

    def __init__(self) -> None:
        self.aborted = False

    def statement(self, *, fails: bool = False) -> None:
        if self.aborted:
            raise RuntimeError("current transaction is aborted")
        if fails:
            self.aborted = True
            raise RuntimeError("statement timeout")


class Games:
    def __init__(self, game: Game) -> None:
        self._game = game

    async def load(self, game_id):
        return self._game if game_id == self._game.game_id else None


class Pairings:
    """``GamesCourtPairing``'s posture: a Levels read that fails is logged and
    answered ``None``."""

    def __init__(self, transaction: Transaction, *, fails: bool = False) -> None:
        self._transaction = transaction
        self._fails = fails
        self.asked = 0

    async def pairing_for(self, *, sport, kind, line_up, reader_id):
        self.asked += 1
        try:
            self._transaction.statement(fails=self._fails)
        except RuntimeError:
            return None
        return Pairing(seats=())


class Tags:
    def __init__(self, transaction: Transaction, *, fails: bool = False) -> None:
        self._transaction = transaction
        self._fails = fails
        self.asked = 0

    async def held_by(self, players):
        self.asked += 1
        self._transaction.statement(fails=self._fails)
        return {player: frozenset({DRINK}) for player in players}


def _a_game(kind: GameKind = GameKind.FRIENDLY) -> Game:
    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=kind,
        window=None,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=OLA),
                Seating(side=GameSide.A, player_id=ANIA),
                Seating(side=GameSide.B, player_id=MAREK),
                Seating(side=GameSide.B, player_id=ZOFIA),
            )
        ),
        occurred_at=instant(NOW - timedelta(days=1)),
        starts_at=instant(NOW + timedelta(days=1)),
    )


def _read(game: Game, pairings: Pairings, tags: Tags) -> ReadGamePairing:
    return ReadGamePairing(
        games=Games(game), pairings=pairings, tags=tags, clock=MovableClock(NOW)
    )


async def test_a_levels_read_that_fails_never_costs_the_vibe():
    transaction = Transaction()
    game = _a_game()
    pairings = Pairings(transaction, fails=True)

    read = await _read(game, pairings, Tags(transaction)).execute(game.game_id, OLA)

    assert read.pairing is None
    assert read.vibe is not None and read.vibe.pct == 100


async def test_a_tags_read_that_fails_is_drawn_as_no_vibe_and_logged(caplog):
    caplog.set_level("WARNING")
    transaction = Transaction()
    game = _a_game()
    pairings = Pairings(transaction)

    read = await _read(game, pairings, Tags(transaction, fails=True)).execute(
        game.game_id, OLA
    )

    assert read.vibe is None
    # The aborted transaction costs the Levels too, and the port answers None.
    assert pairings.asked == 1 and read.pairing is None
    assert any("Social tags" in record.message for record in caplog.records)


async def test_a_competitive_game_asks_no_tags():
    transaction = Transaction()
    game = _a_game(GameKind.COUNTED)
    tags = Tags(transaction)

    read = await _read(game, Pairings(transaction), tags).execute(game.game_id, OLA)

    assert tags.asked == 0
    assert read.vibe is None and read.pairing is not None


async def test_a_court_with_a_seat_open_asks_no_tags():
    transaction = Transaction()
    game = _a_game()
    game.vacate(ZOFIA, occurred_at=instant(NOW))
    tags = Tags(transaction)

    read = await _read(game, Pairings(transaction), tags).execute(game.game_id, OLA)

    assert tags.asked == 0
    assert read.vibe is None
