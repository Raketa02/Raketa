"""**A club's cancel tells the player it never charged** (#711; the telling table
is the only list of what an event tells a player — ``.claude/rules/notifications.md``).

Every player still in a booked game was charged a seat charge, and the charge
already tells them what the cancel did to their money: a held share let go, a
checked one closed, a paid one refunded. So ``ClubCancelled`` tells only the
players it finds with **no** charge on the game — nobody twice. This is the
telling seam itself, with stubs for the ports it reads: the case no HTTP flow
can reach, since every seat booked is charged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from app.application.events import DeliveryContext
from app.kernel import Sport, instant
from app.modules.notifications.application.telling import TOLD_ABOUT, TellThePlayers
from app.modules.notifications.domain.notices import Notice, NoticeKind
from app.modules.notifications.domain.ports import GameBrief
from app.modules.proposals.domain.events import ClubCancelled
from app.shared.ids import new_uuid

NOW = instant(datetime(2026, 10, 9, 19, 0, tzinfo=UTC))
GAME = new_uuid()
OLA, KUBA = new_uuid(), new_uuid()


@dataclass
class Told:
    """Stands in for ``GiveNotice``: records each notice it is asked to give."""

    notices: list[tuple[UUID, Notice]] = field(default_factory=list)

    async def execute(self, player_id: UUID, notice: Notice, *, at: object) -> bool:
        self.notices.append((player_id, notice))
        return True


@dataclass
class Charged:
    """Stands in for ``PaidShares``: who was charged for the game."""

    players: set[UUID]

    async def has_a_charge(self, game_id: UUID, player_id: UUID) -> bool:
        return game_id == GAME and player_id in self.players


@dataclass
class Games:
    """Stands in for ``GameBriefs``: the game as the cancel left it."""

    brief: GameBrief

    async def about(self, game_id: UUID, *, at: object) -> GameBrief | None:
        return self.brief if game_id == GAME else None


def a_cancelled_game() -> GameBrief:
    return GameBrief(
        game_id=GAME,
        pool_id=new_uuid(),
        sport=Sport.PADEL,
        game_kind="COMPETITIVE",
        club_id=new_uuid(),
        starts_at=instant(datetime(2026, 10, 10, 17, 0, tzinfo=UTC)),
        share_grosze=30_00,
        made_at=NOW,
        posted_by=None,
        filling=False,
        open_seats=0,
        in_=(OLA, KUBA),
        withdrawn=(),
        undecided=(),
        named=(),
        booked=False,
        seated=(),
        seats_taken={},
        cancel_reason="WEATHER",
        filled_by=None,
        book_by=NOW,
        fell_back_at=None,
        left_it_short=(),
    )


def teller(told: Told, charged: Charged, brief: GameBrief) -> TellThePlayers:
    return TellThePlayers(
        give=told,  # type: ignore[arg-type]
        games=Games(brief),  # type: ignore[arg-type]
        courts=None,  # type: ignore[arg-type]
        decks=None,  # type: ignore[arg-type]
        shares=charged,  # type: ignore[arg-type]
        offers=None,  # type: ignore[arg-type]
        preferences=None,  # type: ignore[arg-type]
    )


async def test_a_player_never_charged_is_told_the_game_was_called_off():
    told, charged = Told(), Charged(players={OLA})
    event = ClubCancelled(proposal_id=GAME, player_ids=(OLA, KUBA), occurred_at=NOW)

    await teller(told, charged, a_cancelled_game())(
        event, DeliveryContext(event_id=new_uuid(), attempt=1, occurred_at=NOW)
    )

    [(player, notice)] = told.notices
    assert player == KUBA
    assert notice.kind is NoticeKind.GAME_CALLED_OFF
    assert notice.reason == "WEATHER"


async def test_a_player_charged_is_told_by_the_money_not_twice():
    told, charged = Told(), Charged(players={OLA, KUBA})
    event = ClubCancelled(proposal_id=GAME, player_ids=(OLA, KUBA), occurred_at=NOW)

    await teller(told, charged, a_cancelled_game())(
        event, DeliveryContext(event_id=new_uuid(), attempt=1, occurred_at=NOW)
    )

    assert told.notices == []


def test_the_club_cancel_is_listed_in_the_telling_table():
    assert ClubCancelled in TOLD_ABOUT
