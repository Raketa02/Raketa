"""New in Raketa: joiners across the 30 days, and her three relations among
them (#793; the home-rows mechanics §7, §20).

**Why joiners of their own.** The cohort already has members inside the 30
days, but its job is the Games deck's crowd and its ages are the joiner
window's (ADR-0113); none of them is unrated, and none stands in a relation to
her. So this layer writes **eight players outside the cohort**
(:data:`JOINERS`), signed up and through onboarding on the clock their row
names — the way ``seed_the_cohort`` writes the ranking's crowd — and in no
group, so nobody deals them a game:

- **joined today**, no level — *Joined today*, a tile with no sport line;
- **yesterday**, padel and badminton — **she asked them from the row**, so her
  card reads **…** and theirs reads *Found you among new players*;
- **2 days ago**, padel — **they asked her**: the envelope, among the
  unconnected;
- **4 days ago**, no level — **her friend**, at the back of the row;
- 9, 16 and 23 days ago — tennis, nothing, squash — See all's pill;
- **35 days ago**, padel — **stays out** of the row and See all.

**Her relations through the friends' own use cases**, each pair read first, so
a second run asks nobody twice; a request she cancelled in the app is asked
again, as a withdrawn Join request is. The layer drains the outbox itself, so
the directory holds them before the screens are read.

**Re-running writes nothing twice**: every account is found by its address and
a profile already committed records nothing. **Only a fresh store's run is held
to the whole row**: the ages are the first run's, so a run weeks later finds
them older — the 35-day one long out, the rest following — and reports rather
than fails on what time took. ``assert_new_in_raketa`` reads her row and See
all through their own use cases, among the screens.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_accept_friend_request,
    build_ask_to_be_friends,
    build_read_new_in_raketa,
    build_read_new_in_raketa_page,
    build_read_relations,
    build_user_repository,
)
from app.core.config import Settings
from app.kernel import Instant, Sport
from app.modules.discovery.application.new_in_raketa import JoinerCard
from app.modules.discovery.domain.new_in_raketa import ON_THE_ROW
from app.modules.discovery.domain.relation import Relation
from app.modules.friends.application.commands import AnswerCommand, AskCommand
from app.modules.friends.domain.friendship import Where
from app.modules.friends.domain.relation import FriendRelation, RequestOrigin
from app.modules.player_profile.domain.ports import PhotoStorage
from app.modules.player_profile.domain.social_tags import SocialTag
from app.seeds.catalog import CENTRE, THE_POPULATED_PLAYER, dealt_nickname
from app.seeds.clock import FixedClock, hours_before
from app.seeds.cohort import (
    CLUB_PLAYER,
    COHORT,
    COHORT_SEED,
    Cohort,
    CohortMember,
)
from app.seeds.money import THE_FAKE, SeedMoney
from app.seeds.photos import DeclaredVerdict
from app.seeds.ranking_crowd import RANKING_CROWD
from app.seeds.rooms import deliver_everything_told

#: The joiners' second halves — disjoint from the catalog's, the cohort's
#: and the crowd's, so no handle here is one already dealt.
JOINER_SURNAMES: Final[tuple[str, ...]] = ("Lozano", "Marin")

#: Three tags off the served vocabulary, spelled there and nowhere else.
_TAGS: Final = tuple(
    tag.value
    for tag in (
        SocialTag.HERE_TO_MEET_PLAYERS,
        SocialTag.LAUGHS_OFF_MISTAKES,
        SocialTag.STAYS_FOR_A_DRINK,
    )
)

#: A week to commit with — a commit refuses an empty one. In no group, so
#: nobody is dealt it.
_WEEK: Final = ("2:19", "6:10")


@final
@dataclass(frozen=True, slots=True)
class _Row:
    days_ago: int
    sports: tuple[Sport, ...]
    photograph: DeclaredVerdict | None = None


#: Each joiner, by index: when they joined and what they're rated in.
_ROWS: Final[tuple[_Row, ...]] = (
    _Row(days_ago=0, sports=()),
    _Row(
        days_ago=1,
        sports=(Sport.PADEL, Sport.BADMINTON),
        photograph=DeclaredVerdict.ON_A_COURT,
    ),
    _Row(days_ago=2, sports=(Sport.PADEL,), photograph=DeclaredVerdict.NOBODY_LOOKED),
    _Row(days_ago=4, sports=()),
    _Row(days_ago=9, sports=(Sport.TENNIS,)),
    _Row(days_ago=16, sports=()),
    _Row(days_ago=23, sports=(Sport.SQUASH,)),
    _Row(days_ago=35, sports=(Sport.PADEL,)),
)

#: Who stands where with her, by index.
JOINED_TODAY: Final = 0
SHE_ASKED: Final = 1
ASKED_HER: Final = 2
HER_FRIEND: Final = 3
PLAYS_TENNIS: Final = 4
OUT_OF_THE_MONTH: Final = 7


def _member(index: int) -> CohortMember:
    row = _ROWS[index]
    return CohortMember(
        handle=f"joined-{index:02d}",
        ring="joiners",
        archetype=CLUB_PLAYER.name,
        latitude=CENTRE.latitude,
        longitude=CENTRE.longitude,
        slots=_WEEK,
        tags=_TAGS,
        intents=tuple((sport.value, "COMPETITIVE") for sport in row.sports),
        gender="WOMAN" if index % 2 else "MAN",
        gender_preference="ANY",
        committed_days_ago=row.days_ago,
        claims=CLUB_PLAYER.answers.claims,
        demonstrations=CLUB_PLAYER.answers.demonstrations,
        claim_spread=0,
        demonstration_spread=0,
        photograph=None if row.photograph is None else row.photograph.value,
        nickname=dealt_nickname(index, JOINER_SURNAMES),
        intro=None,
    )


#: The joiners, in the shape ``seed_the_cohort`` writes — **not the
#: cohort**: every row above is declared, and ``seed`` is the cohort's own.
JOINERS: Final = Cohort(
    seed=COHORT_SEED,
    members=tuple(_member(index) for index in range(len(_ROWS))),
    centre=COHORT.centre,
)


@final
@dataclass(frozen=True, slots=True)
class SeededJoiners:
    #: Every joiner's id, by index.
    ids: tuple[UUID, ...]
    #: Whether this run wrote them — a fresh store's run, held to the whole row.
    created: bool


async def write_new_in_raketa(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    photos: PhotoStorage,
    photographs: bool,
    money: SeedMoney = THE_FAKE,
) -> SeededJoiners:
    # Imported here: the runner imports this module for its layer.
    from app.seeds.runner import seed_the_cohort

    async with session_factory() as session:
        seeded = await seed_the_cohort(
            session,
            cohort=JOINERS,
            clock=FixedClock(at=now),
            settings=settings,
            photos=photos,
            photographs=photographs,
        )
        her = await _her(session)
    ids = tuple(member.player_id for member in seeded)

    # She asked one of them from the row; one asked her; one is her friend.
    if await _relation(session_factory, her, ids[SHE_ASKED]) is FriendRelation.NONE:
        await _ask(
            session_factory,
            her,
            ids[SHE_ASKED],
            from_=RequestOrigin.NEW_PLAYERS,
            at=hours_before(now, 3),
        )
    if await _relation(session_factory, her, ids[ASKED_HER]) is FriendRelation.NONE:
        await _ask(
            session_factory,
            ids[ASKED_HER],
            her,
            from_=RequestOrigin.RECORD,
            at=hours_before(now, 2),
        )
    if await _relation(session_factory, her, ids[HER_FRIEND]) is FriendRelation.NONE:
        await _ask(
            session_factory,
            ids[HER_FRIEND],
            her,
            from_=RequestOrigin.RECORD,
            at=hours_before(now, 2),
        )
    if (
        await _relation(session_factory, her, ids[HER_FRIEND])
        is FriendRelation.ASKED_YOU
    ):
        async with session_factory() as session:
            await build_accept_friend_request(
                session, clock=hours_before(now, 1)
            ).execute(AnswerCommand(reader_id=her, requester_id=ids[HER_FRIEND]))
    await deliver_everything_told(session_factory, money=money)
    return SeededJoiners(ids=ids, created=all(one.registered for one in seeded))


async def _her(session: AsyncSession) -> UUID:
    user = await build_user_repository(session).get_by_email(THE_POPULATED_PLAYER.email)
    if user is None:
        raise RuntimeError("the protagonist is not registered — the accounts first")
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
    from_: RequestOrigin,
    at: FixedClock,
) -> None:
    async with session_factory() as session:
        await build_ask_to_be_friends(session, clock=at).execute(
            AskCommand(
                requester_id=asker,
                addressee_id=asked,
                where=Where(made_from=from_),
            )
        )


# --------------------------------------------------------------------------- #
# The screen
# --------------------------------------------------------------------------- #


async def assert_new_in_raketa(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    seeded: SeededJoiners,
) -> str:
    """Her row and See all, read through their own use cases — the run fails
    by name unless they hold what this layer promises."""

    clock = FixedClock(at=now)
    async with session_factory() as session:
        her = await _her(session)
        row = await build_read_new_in_raketa(
            session, settings=settings, clock=clock
        ).execute(her)
        everyone: list[JoinerCard] = []
        page = await build_read_new_in_raketa_page(
            session, settings=settings, clock=clock
        ).execute(her, sport=None, after=None)
        everyone.extend(page.cards)
        while page.next is not None:
            page = await build_read_new_in_raketa_page(
                session, settings=settings, clock=clock
            ).execute(her, sport=None, after=page.next)
            everyone.extend(page.cards)
        tennis = await build_read_new_in_raketa_page(
            session, settings=settings, clock=clock
        ).execute(her, sport=Sport.TENNIS, after=None)

    on_the_row = {card.player_id: card for card in row}
    listed = {card.player_id for card in everyone}
    out = seeded.ids[OUT_OF_THE_MONTH]
    if not row or len(row) > ON_THE_ROW:
        raise RuntimeError(f"her New in Raketa row holds {len(row)} cards")
    if out in on_the_row or out in listed:
        raise RuntimeError("the joiner who joined 35 days ago is still new")
    _refuse_a_row_out_of_order(row)
    if not set(on_the_row) <= listed:
        raise RuntimeError("her row holds a joiner See all doesn't list")
    if len(listed) > ON_THE_ROW and len(row) != ON_THE_ROW:
        raise RuntimeError(
            f"{len(listed)} joiners in See all and only {len(row)} on her row"
        )
    if seeded.created:
        expected = {
            JOINED_TODAY: Relation.NONE,
            SHE_ASKED: Relation.SENT,
            ASKED_HER: Relation.ASKED_YOU,
            HER_FRIEND: Relation.FRIEND,
        }
        for index, relation in expected.items():
            card = on_the_row.get(seeded.ids[index])
            if card is None or card.relation is not relation:
                raise RuntimeError(
                    f"joiner {index} is not on her row as {relation.value}: {card}"
                )
        if on_the_row[seeded.ids[JOINED_TODAY]].levels:
            raise RuntimeError("the joiner with no level shows a sport line")
        if seeded.ids[PLAYS_TENNIS] not in {card.player_id for card in tennis.cards}:
            raise RuntimeError("See all's tennis leaves out the tennis joiner")
    return (
        f"New in Raketa: {len(row)} on her row, {len(everyone)} in See all "
        f"(pill: {', '.join(sport.value.title() for sport in page.sports)})"
    )


def _refuse_a_row_out_of_order(row: tuple[JoinerCard, ...]) -> None:
    standing = {
        Relation.NONE: 0,
        Relation.ASKED_YOU: 0,
        Relation.SENT: 1,
        Relation.FRIEND: 2,
    }
    order = [standing[card.relation] for card in row]
    if order != sorted(order):
        raise RuntimeError(
            "her New in Raketa row is not unconnected, then sent, then friends: "
            + ", ".join(f"{card.nickname} {card.relation.value}" for card in row)
        )


def new_in_raketa_lines(seeded: SeededJoiners) -> list[str]:
    lines = ["New in Raketa (#793):"]
    for index, member in enumerate(JOINERS.members):
        row = _ROWS[index]
        sports = ", ".join(sport.value.title() for sport in row.sports) or "no level"
        note = {
            SHE_ASKED: " — she asked them from the row",
            ASKED_HER: " — asked her",
            HER_FRIEND: " — her friend",
            OUT_OF_THE_MONTH: " — out of the 30 days",
        }.get(index, "")
        lines.append(
            f"  {member.nickname} <{member.email}> joined {row.days_ago} day(s) "
            f"before the first run · {sports}{note}"
        )
    if not seeded.created:
        lines.append("  (written by an earlier run: their ages are that run's)")
    return lines


def _refuse_joiners_that_collide() -> None:
    """On import: no joiner's nickname is anybody else's."""

    taken = {member.nickname for member in (*COHORT.members, *RANKING_CROWD.members)}
    for member in JOINERS.members:
        if member.nickname in taken:
            raise RuntimeError(f"'{member.nickname}' is already dealt")


_refuse_joiners_that_collide()
