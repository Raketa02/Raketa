"""Same competitive level: her row read, and a request each way from it
(#794; the home-rows mechanics §6, §9, §12, §20).

**The players around her are already here.** Her padel 3,21 and tennis 3,39
sit in the cohort's thick: members with results and members on the
questionnaire alone at a few hundredths of her, in padel and tennis both, and
two of her padel friends (``rankings.HER_FRIENDS``' ``cohort-a-08`` and
``cohort-a-11``) among the most even. So this layer writes **no player** — a
crowd of its own would only stand between her and them.

**What it writes is the row's two requests**, through the friends' own use
cases, each pair read first so a second run asks nobody twice:

- **she asks** :data:`SHE_ASKS` — six results, 0,05 from her in padel — **from
  the row**, so her card reads **…** among the gaps and theirs *Your level in
  padel · 62% even*;
- :data:`ASKS_HER` — padel and tennis on the questionnaire alone, so the card
  reads *2 sports ›* — **asks her from theirs**, so her Home's request card
  reads the line, and the envelope stands on her row.

**No pair here reads 70% or more** — her own Levels are as unsure as five
results leave anybody (σ ≈ 0,69), and a good match needs a sure level on both
sides — so the row is all gaps, best % first, friends where they fall. The run
says so as a cost rather than failing: it is the engine's Uncertainty, not the
fixture. ``assert_same_level`` reads her row and See all through their own use
cases, among the screens.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_ask_to_be_friends,
    build_read_relations,
    build_read_same_level,
    build_read_same_level_page,
    build_user_repository,
)
from app.core.config import Settings
from app.kernel import Instant, Sport
from app.modules.discovery.application.same_level import SameLevelCard
from app.modules.discovery.domain.relation import Relation
from app.modules.discovery.domain.same_level import (
    ON_THE_ROW,
    SameLevelPlayer,
    is_fresh,
)
from app.modules.discovery.domain.totals import capped
from app.modules.friends.application.commands import AskCommand
from app.modules.friends.domain.friendship import Where
from app.modules.friends.domain.relation import FriendRelation, RequestOrigin
from app.seeds.catalog import THE_POPULATED_PLAYER
from app.seeds.clock import FixedClock, hours_before
from app.seeds.cohort import COHORT
from app.seeds.money import THE_FAKE, SeedMoney
from app.seeds.rooms import deliver_everything_told

#: Who she asks from her row: six padel results, a few hundredths above her.
SHE_ASKS: Final = "cohort-c-01"
#: Who asks her from theirs: padel and tennis from the questionnaire alone.
ASKS_HER: Final = "cohort-b-03"
#: The sport each request names — the card's.
ASKED_IN: Final = Sport.PADEL


@final
@dataclass(frozen=True, slots=True)
class SeededSameLevel:
    she_asked: UUID
    asked_her: UUID
    #: Whether this run asked either — a fresh store's run, held to both.
    created: bool
    #: Fresh good matches on her row when the screens were read (``None``
    #: before): none, while nobody is sure enough to read 70%.
    fresh: int | None = None


async def write_same_level(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    now: Instant,
    money: SeedMoney = THE_FAKE,
) -> SeededSameLevel:
    async with session_factory() as session:
        her = await _id_of(session, THE_POPULATED_PLAYER.email)
        she_asks = await _id_of(session, COHORT.by_handle(SHE_ASKS).email)
        asks_her = await _id_of(session, COHORT.by_handle(ASKS_HER).email)
    created = False
    if await _relation(session_factory, her, she_asks) is FriendRelation.NONE:
        await _ask(session_factory, her, she_asks, at=hours_before(now, 2))
        created = True
    if await _relation(session_factory, her, asks_her) is FriendRelation.NONE:
        await _ask(session_factory, asks_her, her, at=hours_before(now, 1))
        created = True
    await deliver_everything_told(session_factory, money=money)
    return SeededSameLevel(she_asked=she_asks, asked_her=asks_her, created=created)


async def _id_of(session: AsyncSession, email: str) -> UUID:
    user = await build_user_repository(session).get_by_email(email)
    if user is None:
        raise RuntimeError(f"{email} is not registered — the accounts run first")
    return user.id


async def _relation(
    session_factory: async_sessionmaker[AsyncSession], reader: UUID, other: UUID
) -> FriendRelation:
    async with session_factory() as session:
        relations = await build_read_relations(session).relations_of(reader, [other])
    return relations[other]


async def _ask(
    session_factory: async_sessionmaker[AsyncSession],
    asker: UUID,
    asked: UUID,
    *,
    at: FixedClock,
) -> None:
    async with session_factory() as session:
        await build_ask_to_be_friends(session, clock=at).execute(
            AskCommand(
                requester_id=asker,
                addressee_id=asked,
                where=Where(made_from=RequestOrigin.SAME_LEVEL, sport=ASKED_IN),
            )
        )


# --------------------------------------------------------------------------- #
# The screen
# --------------------------------------------------------------------------- #


async def assert_same_level(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    seeded: SeededSameLevel,
) -> tuple[str, SeededSameLevel]:
    """Her row and every See all page, read through their own use cases — the
    run fails by name unless they hold what this layer promises."""

    async with session_factory() as session:
        her = await _id_of(session, THE_POPULATED_PLAYER.email)
        read = await build_read_same_level(session, settings=settings).execute(her)
        row = read.cards
        everyone: list[SameLevelCard] = []
        page = await build_read_same_level_page(session, settings=settings).execute(
            her, sport=None, after=None
        )
        everyone.extend(page.cards)
        while page.next is not None:
            page = await build_read_same_level_page(session, settings=settings).execute(
                her, sport=None, after=page.next
            )
            everyone.extend(page.cards)

    if not row or len(row) > ON_THE_ROW:
        raise RuntimeError(f"her Same competitive level row holds {len(row)} cards")
    if len(row) != min(ON_THE_ROW, len(everyone)):
        raise RuntimeError(
            f"{len(everyone)} players in See all and {len(row)} on her row"
        )
    if read.total != capped(len(everyone)):
        raise RuntimeError(
            f"her Same competitive level line counts {read.total} and See all "
            f"lists {len(everyone)}"
        )
    listed = {card.player_id for card in everyone}
    if not {card.player_id for card in row} <= listed:
        raise RuntimeError("her row holds a player See all doesn't list")
    _refuse_an_order_the_rule_does_not_make(row, everyone)
    relations = {card.player_id: card.relation for card in everyone}
    if sum(relation is Relation.FRIEND for relation in relations.values()) < 2:
        raise RuntimeError("fewer than two of her friends share a sport with her")
    if seeded.created:
        for player, relation in (
            (seeded.she_asked, Relation.SENT),
            (seeded.asked_her, Relation.ASKED_YOU),
        ):
            if relations.get(player) is not relation:
                raise RuntimeError(
                    f"{player} is not on her Same level list as {relation.value}"
                )
    fresh = sum(is_fresh(_as_player(card), card.relation, rested=False) for card in row)
    return (
        f"Same competitive level: {len(row)} on her row of {read.total} "
        f"({fresh} fresh), "
        f"{len(everyone)} in See all, best "
        f"{everyone[0].shown.percent_even}% (pill: "
        f"{', '.join(sport.value.title() for sport in page.sports)})"
    ), SeededSameLevel(
        she_asked=seeded.she_asked,
        asked_her=seeded.asked_her,
        created=seeded.created,
        fresh=fresh,
    )


def _as_player(card: SameLevelCard) -> SameLevelPlayer:
    return SameLevelPlayer(
        player_id=card.player_id, shown=card.shown, comparisons=card.comparisons
    )


def _refuse_an_order_the_rule_does_not_make(
    row: tuple[SameLevelCard, ...], everyone: list[SameLevelCard]
) -> None:
    keys = [_as_player(card).key.order for card in everyone]
    if keys != sorted(keys):
        raise RuntimeError("her See all is not best % first")
    fresh = [is_fresh(_as_player(card), card.relation, rested=False) for card in row]
    if fresh != sorted(fresh, reverse=True):
        raise RuntimeError("her row has a gap before a fresh good match")
    for part in (
        [card for card, one in zip(row, fresh, strict=True) if one],
        [card for card, one in zip(row, fresh, strict=True) if not one],
    ):
        order = [_as_player(card).key.order for card in part]
        if order != sorted(order):
            raise RuntimeError(
                "her Same competitive level row is not best % first within "
                "its fresh matches and its gaps: "
                + ", ".join(
                    f"{card.nickname} {card.shown.percent_even}%" for card in part
                )
            )


def same_level_lines(seeded: SeededSameLevel) -> list[str]:
    she = COHORT.by_handle(SHE_ASKS)
    asker = COHORT.by_handle(ASKS_HER)
    lines = [
        "Same competitive level (#794):",
        f"  she asked {she.nickname} <{she.email}> from her row, in padel",
        f"  {asker.nickname} <{asker.email}> asked her from theirs, in padel — "
        "her Home reads the line",
    ]
    if not seeded.created:
        lines.append("  (asked by an earlier run)")
    return lines
