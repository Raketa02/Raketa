"""Reading games back asks **once** about everybody, and never once per seat.

The claim lives in three docstrings — ``PlayerNames``, ``ReadGames.execute``
and ``docs/adr/0141`` §4 — and it is the kind of claim that goes quietly wrong:
a handle read inside the loop that renders a seat is correct on every screen and
costs sixteen round trips on a list of four doubles games. Nothing else in the
suite would notice, because the answer would be identical.

The second half is the shape of a missing one. A player ``users`` can no longer
answer for **keeps their seat** — the opposite of the shortlist, where a card
with no name is not a card and the row is dropped — because a court with a
seat taken out of it is a three-person doubles game.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Collection, Mapping
from uuid import UUID

from app.kernel import Instant, Sport, instant
from app.modules.games.application.read_games import ReadGames
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.shared.ids import new_uuid

NOW = instant(datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc))


class FixedClock:
    def now(self) -> Instant:
        return NOW


@dataclass
class Directory:
    """``GameDirectory`` over a list somebody wrote by hand."""

    games: tuple[Game, ...] = ()

    async def playing(self, player_id: UUID) -> tuple[Game, ...]:
        return self.games


@dataclass
class Handles:
    """``PlayerNames`` over a dict, remembering **every** question it was asked."""

    known: Mapping[UUID, str] = field(default_factory=dict)
    asked: list[tuple[UUID, ...]] = field(default_factory=list)

    async def names_of(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, str]:
        # **The order is recorded, not just the membership.** A ``frozenset``
        # here would make the file unable to notice the one thing
        # ``docs/adr/0105`` §1 is about.
        self.asked.append(tuple(player_ids))
        return {
            player_id: self.known[player_id]
            for player_id in player_ids
            if player_id in self.known
        }


def a_game(*players: UUID, at: Instant = NOW) -> Game:
    """One doubles game, the first two players on side A and the rest on B."""

    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=None,
        line_up=LineUp.of(
            Seating(
                side=GameSide.A if at_seat < 2 else GameSide.B,
                player_id=player_id,
            )
            for at_seat, player_id in enumerate(players)
        ),
        occurred_at=at,
    )


async def test_one_question_for_a_whole_list_and_never_one_per_seat():
    """**Sixteen people across four games is one read**, over the union.

    A player on three of your courts is asked about once, which is the half a
    per-game read would also get wrong.
    """

    me, partner, one, two = (new_uuid() for _ in range(4))
    three, four = new_uuid(), new_uuid()
    directory = Directory(
        games=(
            a_game(me, partner, one, two, at=NOW),
            a_game(me, partner, three, four, at=instant(NOW - timedelta(days=1))),
        )
    )
    names = Handles(
        known={
            me: "me_",
            partner: "kasia_w",
            one: "tomek.p",
            two: "marekb",
            three: "bea_k",
            four: "dorota_w",
        }
    )

    _, found = await ReadGames(
        games=directory, names=names, clock=FixedClock()
    ).execute(me)

    assert names.asked == [tuple(sorted({me, partner, one, two, three, four}))], (
        "a read per game — or per seat — answers the same and costs a round trip "
        "each; and the union is handed over in an order, never as a set "
        "(``docs/adr/0105`` §1)"
    )
    assert all(one_game.names[me] == "me_" for one_game in found), (
        "every game in the list is folded against the one answer"
    )


async def test_an_empty_list_asks_about_nobody_rather_than_not_asking():
    """Nought games is nought people, and **the question is still asked.**

    Where the round trip is not spent is in the adapter, which answers an empty
    collection without going near the database — so the saving is real and it is
    one layer down. Spelling that here rather than short-circuiting in the use
    case keeps one rule at the port instead of two half-rules either side of it.
    """

    names = Handles()

    _, found = await ReadGames(
        games=Directory(), names=names, clock=FixedClock()
    ).execute(new_uuid())

    assert found == ()
    assert names.asked == [()]


async def test_a_player_users_cannot_answer_for_keeps_their_seat():
    """**The opposite of the shortlist's rule, and deliberately.**

    A card with no name is not a card, so that row goes. A seat with no
    name is still somebody who was on the court, so it stays and the name
    is what goes missing (``docs/adr/0141`` §3).
    """

    me, partner, one, two = (new_uuid() for _ in range(4))
    names = Handles(known={me: "me_", partner: "kasia_w", one: "tomek.p"})

    _, (found,) = await ReadGames(
        games=Directory(games=(a_game(me, partner, one, two),)),
        names=names,
        clock=FixedClock(),
    ).execute(me)

    assert len(found.game.line_up.seatings) == 4
    assert two not in found.names


async def test_the_leaver_who_called_it_off_is_named_though_their_seat_is_open():
    """``docs/adr/0172`` §4 — ``called_off_by`` is one more id in the union the
    read already asks about, because the leaver's seat is **vacated** on the
    game and the court cannot supply the name."""

    me, partner, one, two = (new_uuid() for _ in range(4))
    game = a_game(me, partner, one, two, at=NOW)
    game.vacate(two, occurred_at=instant(NOW - timedelta(hours=2)))
    game.call_off(by=two, occurred_at=instant(NOW - timedelta(hours=1)))
    names = Handles(
        known={me: "me_", partner: "kasia_w", one: "tomek.p", two: "marekb"}
    )

    _, found = await ReadGames(
        games=Directory(games=(game,)), names=names, clock=FixedClock()
    ).execute(me)

    assert names.asked == [tuple(sorted({me, partner, one, two}))]
    (row,) = found
    assert row.game.called_off_by == two
    assert row.names[two] == "marekb"


async def test_a_game_the_reader_dismissed_is_left_off_their_rail_and_nobody_elses():
    """``docs/adr/0172`` §5 — derived on every read: the aggregate folds who
    has dismissed it and the rail subtracts its reader. The other players'
    rails are untouched, and so is the record."""

    me, partner, one, two = (new_uuid() for _ in range(4))
    game = a_game(me, partner, one, two, at=NOW)
    game.vacate(two, occurred_at=instant(NOW - timedelta(hours=2)))
    game.call_off(by=two, occurred_at=instant(NOW - timedelta(hours=1)))
    game.dismiss(by=me, occurred_at=instant(NOW - timedelta(minutes=5)))
    directory = Directory(games=(game,))
    names = Handles(known={me: "me_", partner: "kasia_w", one: "tomek.p"})

    _, mine = await ReadGames(games=directory, names=names, clock=FixedClock()).execute(
        me
    )
    _, theirs = await ReadGames(
        games=directory, names=names, clock=FixedClock()
    ).execute(partner)

    assert mine == ()
    assert [row.game.id for row in theirs] == [game.id]
