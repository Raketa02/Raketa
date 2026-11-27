"""Same vibe players: her row read, and a request each way from it (#795; the
home-rows mechanics §8, §9, §12, §20).

**The players sharing her tags are already here.** She holds six
(``catalog.HER_TAGS``), and the cohort's own draws meet them at every count from
one to six — ``cohort-a-01`` holds all six, ``cohort-a-15`` and ``cohort-d-07``
five, five members four (the cohort's draw from all twenty-seven tags, #832) —
while the ranking's crowd shares two and the New in Rakieta joiners none. Her
friends share one, three and four. So this layer writes **no player**, as Same
competitive level's doesn't.

**Her six tags are the catalog's**, committed with her profile on a fresh
store. A store seeded before #795 committed her three, one seeded before #832
her old six, and a commit is
idempotent, so this layer **changes her tags through the You tab's own use case**
— which records nothing when they are already hers — before anything reads them.

**What it writes is the row's two requests**, through the friends' own use
cases, each pair read first so a second run asks nobody twice:

- **she asks** :data:`SHE_ASKS` — five tags in common — **from the row**, so
  their Home reads *5 things in common*;
- :data:`ASKS_HER` — all six — **asks her from theirs**, so her Home's request
  card reads *6 things in common*, and the envelope stands first on her row.

**A store seeded before #832 keeps the two requests that run made** — hers to
``cohort-a-13`` and ``cohort-d-01``'s to her — beside these two, since the
names moved with the redraw and nothing here takes a request back: her Home
then reads two *Found you through your tags* cards, each counted today. A fresh
store holds these two alone.

**Her row is all fresh**: the cohort and the ranking's crowd hold far more than
ten unconnected players sharing two tags with her or more, so her friends and
her request wait in See all, where they fall, and never reach a gap. The run
counts it. ``assert_same_vibe`` reads her row and See all through their own use
cases, among the screens.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_ask_to_be_friends,
    build_domain_event_store,
    build_event_publisher,
    build_player_profile_repository,
    build_read_relations,
    build_read_same_vibe,
    build_read_same_vibe_page,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings
from app.kernel import Instant
from app.modules.discovery.application.same_vibe import SameVibeCard
from app.modules.discovery.domain.relation import Relation
from app.modules.discovery.domain.same_vibe import (
    ON_THE_ROW,
    is_fresh,
    is_good_match,
)
from app.modules.discovery.domain.totals import capped
from app.modules.friends.application.commands import AskCommand
from app.modules.friends.domain.friendship import Where
from app.modules.friends.domain.relation import FriendRelation, RequestOrigin
from app.modules.player_profile.application.change_social_tags import (
    ChangeSocialTags,
)
from app.modules.player_profile.application.commands import ChangeSocialTagsCommand
from app.seeds.catalog import HER_TAGS, THE_POPULATED_PLAYER
from app.seeds.clock import FixedClock, hours_before
from app.seeds.cohort import COHORT
from app.seeds.money import THE_FAKE, SeedMoney
from app.seeds.rooms import deliver_everything_told

#: Who she asks from her row: five of her six tags.
SHE_ASKS: Final = "cohort-a-15"
#: Who asks her from theirs: all six.
ASKS_HER: Final = "cohort-a-01"
#: Every count of shared tags her See all must hold — a player holds at most six.
EVERY_COUNT: Final = range(1, len(HER_TAGS) + 1)


@final
@dataclass(frozen=True, slots=True)
class SeededSameVibe:
    she_asked: UUID
    asked_her: UUID
    #: Whether this run asked either — a fresh store's run, held to both.
    created: bool
    #: Whether this run gave her the six tags — a store seeded before #795 or
    #: before #832 re-picked three of them.
    retagged: bool
    #: Fresh good matches on her row when the screens were read (``None``
    #: before).
    fresh: int | None = None


async def write_same_vibe(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    now: Instant,
    money: SeedMoney = THE_FAKE,
) -> SeededSameVibe:
    async with session_factory() as session:
        her = await _id_of(session, THE_POPULATED_PLAYER.email)
        she_asks = await _id_of(session, COHORT.by_handle(SHE_ASKS).email)
        asks_her = await _id_of(session, COHORT.by_handle(ASKS_HER).email)
    retagged = await _her_tags(session_factory, her, now=now)
    created = False
    if await _relation(session_factory, her, she_asks) is FriendRelation.NONE:
        await _ask(session_factory, her, she_asks, at=hours_before(now, 2))
        created = True
    if await _relation(session_factory, her, asks_her) is FriendRelation.NONE:
        await _ask(session_factory, asks_her, her, at=hours_before(now, 1))
        created = True
    await deliver_everything_told(session_factory, money=money)
    return SeededSameVibe(
        she_asked=she_asks, asked_her=asks_her, created=created, retagged=retagged
    )


async def _her_tags(
    session_factory: async_sessionmaker[AsyncSession], her: UUID, *, now: Instant
) -> bool:
    """Her six, through *Edit tags*' own use case — whether they changed."""

    async with session_factory() as session:
        profiles = build_player_profile_repository(
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        )
        before = await profiles.load(her)
        if before is None:
            raise RuntimeError("she holds no Player profile — the accounts run first")
        if set(before.social_tags.ids) == set(HER_TAGS):
            return False
        await ChangeSocialTags(
            profiles=profiles, uow=build_unit_of_work(session), clock=FixedClock(now)
        ).execute(ChangeSocialTagsCommand(player_id=her, social_tag_ids=HER_TAGS))
        return True


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
                where=Where(made_from=RequestOrigin.SAME_VIBE),
            )
        )


# --------------------------------------------------------------------------- #
# The screen
# --------------------------------------------------------------------------- #


async def assert_same_vibe(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    seeded: SeededSameVibe,
) -> tuple[str, SeededSameVibe]:
    """Her row and every See all page, read through their own use cases — the
    run fails by name unless they hold what this layer promises."""

    async with session_factory() as session:
        her = await _id_of(session, THE_POPULATED_PLAYER.email)
        read = await build_read_same_vibe(session, settings=settings).execute(her)
        row = read.cards
        everyone: list[SameVibeCard] = []
        page = await build_read_same_vibe_page(session, settings=settings).execute(
            her, sport=None, after=None
        )
        everyone.extend(page.cards)
        while page.next is not None:
            page = await build_read_same_vibe_page(session, settings=settings).execute(
                her, sport=None, after=page.next
            )
            everyone.extend(page.cards)

    if not row or len(row) > ON_THE_ROW:
        raise RuntimeError(f"her Same vibe row holds {len(row)} cards")
    if len(row) != min(ON_THE_ROW, len(everyone)):
        raise RuntimeError(
            f"{len(everyone)} players in her Same vibe See all and {len(row)} "
            "on her row"
        )
    if read.total != capped(len(everyone)):
        raise RuntimeError(
            f"her Same vibe line counts {read.total} and See all lists {len(everyone)}"
        )
    if not {card.player_id for card in row} <= {card.player_id for card in everyone}:
        raise RuntimeError("her Same vibe row holds a player See all doesn't list")
    _refuse_an_order_the_rule_does_not_make(row, everyone)
    counts = Counter(card.in_common for card in everyone)
    missing = [n for n in EVERY_COUNT if not counts[n]]
    if missing:
        raise RuntimeError(
            "nobody in her Same vibe See all shares "
            + ", ".join(str(n) for n in missing)
            + " of her tags — the cohort's draws no longer meet "
            "catalog.HER_TAGS at every count"
        )
    good = [card for card in everyone if is_good_match(card.in_common)]
    if not any(card.relation is Relation.FRIEND for card in good):
        raise RuntimeError("no friend of hers shares two tags with her or more")
    if seeded.created:
        relations = {card.player_id: card.relation for card in everyone}
        for player, relation in (
            (seeded.she_asked, Relation.SENT),
            (seeded.asked_her, Relation.ASKED_YOU),
        ):
            if relations.get(player) is not relation:
                raise RuntimeError(
                    f"{player} is not on her Same vibe list as {relation.value}"
                )
    fresh = sum(_is_fresh(card) for card in row)
    return (
        f"Same vibe: {len(row)} on her row of {read.total} ({fresh} fresh), "
        f"{len(everyone)} in "
        f"See all — "
        + ", ".join(f"{counts[n]} sharing {n}" for n in reversed(EVERY_COUNT))
        + f" (pill: {', '.join(sport.value.title() for sport in page.sports)})"
    ), SeededSameVibe(
        she_asked=seeded.she_asked,
        asked_her=seeded.asked_her,
        created=seeded.created,
        retagged=seeded.retagged,
        fresh=fresh,
    )


def _is_fresh(card: SameVibeCard) -> bool:
    """§9's rule as the row applies it, nobody resting yet (#796)."""

    return is_fresh(card.in_common, card.relation, rested=False)


def _refuse_an_order_the_rule_does_not_make(
    row: tuple[SameVibeCard, ...], everyone: list[SameVibeCard]
) -> None:
    shared = [card.in_common for card in everyone]
    if shared != sorted(shared, reverse=True):
        raise RuntimeError("her Same vibe See all is not most in common first")
    position = {card.player_id: n for n, card in enumerate(everyone)}
    fresh = [_is_fresh(card) for card in row]
    if fresh != sorted(fresh, reverse=True):
        raise RuntimeError("her Same vibe row has a gap before a fresh good match")
    for part in (
        [card for card, one in zip(row, fresh, strict=True) if one],
        [card for card, one in zip(row, fresh, strict=True) if not one],
    ):
        order = [position[card.player_id] for card in part]
        if order != sorted(order):
            raise RuntimeError(
                "her Same vibe row is not in See all's order within its fresh "
                "matches and its gaps: "
                + ", ".join(f"{card.nickname} {card.in_common}" for card in part)
            )


def same_vibe_lines(seeded: SeededSameVibe) -> list[str]:
    she = COHORT.by_handle(SHE_ASKS)
    asker = COHORT.by_handle(ASKS_HER)
    lines = [
        "Same vibe (#795):",
        f"  she holds six tags: {', '.join(HER_TAGS)}",
        f"  she asked {she.nickname} <{she.email}> from her row — five in common",
        f"  {asker.nickname} <{asker.email}> asked her from theirs — six in "
        "common, her Home reads the line",
    ]
    if seeded.retagged:
        lines.append(
            "  (given them this run — a store seeded before #795 held her three, "
            "one before #832 her old six)"
        )
    if not seeded.created:
        lines.append("  (asked by an earlier run)")
    return lines
