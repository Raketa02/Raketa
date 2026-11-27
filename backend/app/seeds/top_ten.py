"""Top 10: squash with exactly two listed players, and her row read in every
state (#797; the home-rows mechanics §10, §20).

**What the row needs that no other layer writes.** Top 10 has three states to
walk — ten cards, one or two, nobody — and the ranking's seed already gives two
of them: **padel** lists sixty-two (``rankings.py``), and **badminton** nobody.
**Tennis** lists the beginner, and her beside them once the API's first tick
confirms the evening she left unanswered — and her trophy's sport is tennis,
her evenings being her latest results, so **her Home's Top 10 opens on tennis,
with her own card there once the API has started**. Padel can't hold her among
its ten as well: the ranking's crowd puts her 56th, below the Rankings page's
first page, for *You · 56th* (#770). **Squash lists nobody**: nobody in the
cohort plays it. So this layer writes the *one or two* state on purpose, in
squash, and never moves a padel or tennis place.

**Two players of its own, outside the cohort** (:data:`SQUASH_PAIR`), as the
ranking's crowd is: the histogram, the aging refusal and every deck never see
them. Registered and named, **rated in squash by sitting the questionnaire**
(``seed_the_cohort``, beside the crowd, one answer set for both so each is
inside the other's competitive window), a profile committed **sixty days ago**
— out of New in Rakieta's month — and their week **cleared** after it, so the
proposer deals neither of them; a card each, saved by the payment layer. **No
tag of hers** and no padel or tennis level, so no row of hers reads them: Same
competitive level compares only a sport two players share, and Same vibe a
tag.

**Five squash results between them** (:data:`SQUASH_GAMES`), each **a past
booked game** on Prądnik Tennis's squash court — Ogrody 33, where the history
plays, has none, and a squash club on the default three-day release lead gives
its hours back before the two days ahead a history game is made — in *Squash na
Prądniku*, a group the first runs and the second joined: placed,
made, filled by both yeses, the cut-off job run at its cut-off, played,
scored and accepted through the played history's own path
(``booked_history.write_games_among``). The agreement's delivery moves both
Levels and folds both rows, so squash lists exactly the two, each on five
results. **A group of two**, so Hottest groups leaves it out. Played 40 to 32
days ago, one game every other day: listed for the 90 days after the last,
before her week whatever the weekday, and neither of them *New*.

**Re-running writes nothing twice**: the people are found by address, the group
is its Owner's of that name at that club, joining again records nothing, and a
game is found again as the played history finds one.

**Her row, read in every state** (``assert_the_top_ten``, among the screens):
preferring her trophy's sport it opens with cards — with her own where she is
placed among them; padel reads ten cards, places 1 to 10; squash the two;
badminton none, with somebody listed elsewhere. **Ten cards with your own among
them** is walked as the ranking's crowd player placed 7th in padel, whom the
screen line names to sign in as. Any of it missing fails the run by name.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_general_orders_kept_here,
    build_group_code_minter,
    build_home_clubs,
    build_read_home_ranking,
    build_read_top_ten,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings
from app.kernel import Instant, Sport, instant
from app.modules.clubs.domain.court_hours import CLUB_ZONE
from app.modules.groups.application.commands import CreatePlayerGroupCommand
from app.modules.groups.application.create_player_group import CreatePlayerGroup
from app.modules.groups.domain.value_objects import GroupName, JoinPolicy
from app.modules.player_profile.domain.social_tags import SocialTag
from app.modules.rankings.application.reads import TopTen
from app.modules.rankings.domain.ranking import GENERAL_ENTRY, LISTED_FOR
from app.modules.rankings.domain.top_ten import TOP_TEN
from app.seeds.booked_history import MADE_AHEAD, WrittenGame, write_games_among
from app.seeds.bookings import club_id_of
from app.seeds.catalog import (
    CATALOG_SURNAMES,
    CENTRE,
    COHORT_SURNAMES,
    HER_TAGS,
    THE_POPULATED_PLAYER,
    dealt_nickname,
)
from app.seeds.clock import FixedClock
from app.seeds.clubs import SEED_CLUBS
from app.seeds.cohort import (
    CLUB_PLAYER,
    COHORT,
    COHORT_SEED,
    Cohort,
    CohortMember,
    PlayedGame,
)
from app.seeds.groups import group_repository, group_run_by, join_group
from app.seeds.money import THE_FAKE, SeedMoney
from app.seeds.new_in_rakieta import JOINER_SURNAMES, JOINERS
from app.seeds.ranking_crowd import CROWD_SURNAMES, RANKING_CROWD
from app.seeds.rankings import EMPTY_SPORT, RANKED_SPORT

#: The sport this layer lists two in.
PAIRED_SPORT: Final = Sport.SQUASH
#: Where they play: a club that sells squash and keeps its hours Rakieta's
#: until a day before — past the two days ahead a history game is made.
SQUASH_CLUB: Final = next(club for club in SEED_CLUBS if club.name == "Prądnik Tennis")
#: Their group there, run by the first of them.
SQUASH_GROUP: Final = "Squash na Prądniku"
GroupName(SQUASH_GROUP)

#: The pair's second halves — disjoint from every other pool, so no handle here
#: is one already dealt.
SQUASH_SURNAMES: Final[tuple[str, ...]] = ("Tejero",)

#: Committed this long before the run — before the first game was made, and out
#: of New in Rakieta's 30 days and the newcomer's 14.
_COMMITTED_DAYS_AGO: Final = 60

#: Three tags, **none of hers**, so Same vibe never reads them to her.
_TAGS: Final = tuple(
    tag.value
    for tag in (
        SocialTag.QUIET_AND_FOCUSED,
        SocialTag.HERE_TO_COMPETE,
        SocialTag.STRAIGHT_HOME_AFTER,
    )
)

#: A week to commit with — a commit refuses an empty one — cleared after it.
_COMMITTED_WEEK: Final = ("2:19", "6:10")

#: One answer set for both — (claims, demonstrations), no spread — so they
#: start level, inside each other's competitive window.
_ANSWERS: Final = (3, 3)

#: The days the five games were played, in days before the run.
_GAME_DAYS_AGO: Final = (40, 38, 36, 34, 32)

#: The padel place whose crowd player the report names for *ten cards with
#: your own among them* — the issue's story's 7th.
WALKED_AT: Final = 7


def _member(index: int) -> CohortMember:
    claims, demonstrations = _ANSWERS
    return CohortMember(
        handle=f"squash-{index:02d}",
        ring="squash",
        archetype=CLUB_PLAYER.name,
        latitude=CENTRE.latitude,
        longitude=CENTRE.longitude,
        slots=_COMMITTED_WEEK,
        tags=_TAGS,
        intents=((PAIRED_SPORT.value, "COMPETITIVE"),),
        gender="WOMAN" if index % 2 else "MAN",
        gender_preference="ANY",
        committed_days_ago=_COMMITTED_DAYS_AGO,
        claims=claims,
        demonstrations=demonstrations,
        claim_spread=0,
        demonstration_spread=0,
        photograph=None,
        nickname=dealt_nickname(index, SQUASH_SURNAMES),
        intro=None,
    )


#: The pair, in the shape ``seed_the_cohort`` writes — **not the cohort**: every
#: row above is declared, and ``seed`` is the cohort's own.
SQUASH_PAIR: Final = Cohort(
    seed=COHORT_SEED,
    members=tuple(_member(index) for index in range(2)),
    centre=COHORT.centre,
)

_FIRST, _SECOND = (member.handle for member in SQUASH_PAIR.members)

#: **Their five results, oldest first**: singles, the first declared player
#: winning three and the second two.
SQUASH_GAMES: Final[tuple[PlayedGame, ...]] = tuple(
    PlayedGame(
        sport=PAIRED_SPORT.value,
        played_days_ago=days_ago,
        side_a=(_FIRST,),
        side_b=(_SECOND,),
        won_by="A" if index % 2 == 0 else "B",
    )
    for index, days_ago in enumerate(_GAME_DAYS_AGO)
)


def _refuse_a_pair_that_cannot_be_listed() -> None:
    """On import: nobody else's nickname, none of her tags, five results each
    inside the 90 days, every game made after both committed."""

    taken = {
        member.nickname
        for member in (*COHORT.members, *RANKING_CROWD.members, *JOINERS.members)
    }
    pools = (CATALOG_SURNAMES, COHORT_SURNAMES, CROWD_SURNAMES, JOINER_SURNAMES)
    if any(set(SQUASH_SURNAMES) & set(pool) for pool in pools):
        raise RuntimeError("the squash pair's surnames are another pool's")
    for member in SQUASH_PAIR.members:
        if member.nickname in taken:
            raise RuntimeError(f"'{member.nickname}' is already dealt")
        if set(member.tags) & set(HER_TAGS):
            raise RuntimeError(f"'{member.handle}' holds a tag of hers")
    if len(SQUASH_GAMES) != GENERAL_ENTRY:
        raise RuntimeError(f"the pair play {GENERAL_ENTRY} results, no more")
    for game in SQUASH_GAMES:
        if game.played_days_ago >= LISTED_FOR.days:
            raise RuntimeError("a squash game is older than the 90 days")
        if _COMMITTED_DAYS_AGO <= game.played_days_ago + MADE_AHEAD.days:
            raise RuntimeError("a squash game was made before the pair committed")
    if len(set(_GAME_DAYS_AGO)) != len(_GAME_DAYS_AGO):
        raise RuntimeError("the pair play twice on one day")


_refuse_a_pair_that_cannot_be_listed()


class TopTenIsWrong(RuntimeError):
    """The row a tester signs in to read is not the one this layer promises."""


@final
@dataclass(frozen=True, slots=True)
class SeededSquashPair:
    group_id: UUID
    #: Whether this run created the group, or found it already there.
    created: bool
    games: tuple[WrittenGame, ...]


async def write_the_squash_pair(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    money: SeedMoney = THE_FAKE,
) -> SeededSquashPair:
    """Their group and their five games — **after the played history**, so the
    rooms layer's drain folds their rows with everybody's, and after the pair
    themselves, their cards and the clubs' courts, which it reads and never
    writes."""

    first, second = SQUASH_PAIR.members
    async with session_factory() as session:
        owner = await _id_of(session, first.email)
        member = await _id_of(session, second.email)
        club_id = await club_id_of(session, SQUASH_CLUB)
        opened = instant(
            now - timedelta(days=first.committed_days_ago) + timedelta(minutes=30)
        )
        group_id = await group_run_by(
            session, owner, club_id=club_id, name=SQUASH_GROUP
        )
        created = group_id is None
        if group_id is None:
            group_id = await CreatePlayerGroup(
                groups=group_repository(session),
                clubs=build_home_clubs(session),
                codes=build_group_code_minter(session),
                uow=build_unit_of_work(session),
                clock=FixedClock(at=opened),
            ).execute(
                CreatePlayerGroupCommand(
                    creator_id=owner,
                    name=SQUASH_GROUP,
                    home_club_id=club_id,
                    join_policy=JoinPolicy.ANYONE,
                )
            )
        await join_group(
            session,
            settings,
            group_id,
            member,
            FixedClock(at=instant(opened + timedelta(minutes=30))),
        )
    games = await write_games_among(
        session_factory,
        settings=settings,
        now=now,
        games=SQUASH_GAMES,
        players=SQUASH_PAIR.members,
        group_id=group_id,
        club=SQUASH_CLUB,
        money=money,
    )
    return SeededSquashPair(group_id=group_id, created=created, games=games)


async def assert_the_top_ten(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
) -> str:
    """Her Top 10, read through its own use case in each state — **opening on
    her trophy's sport, or the sport it falls through to, with cards; padel ten
    cards; squash the pair; badminton none** — or the run fails by name. The
    screen line.

    **Her own card is held to it only where she is placed in the top ten**: on
    the run that writes her evenings, her fifth tennis result is the score she
    left unanswered, which the rating catch-up confirms on the API's first
    tick — so tennis lists the beginner alone until the API starts, and her
    beside them after it, on every later run.

    **Ten cards with your own among them** can't be hers — padel puts her 56th
    — so the line names the ranking's crowd player placed :data:`WALKED_AT` in
    padel, whose row opens there, their trophy's only sport, with their own
    card: a seed account a tester signs in as."""

    async with session_factory() as session:
        orders = build_general_orders_kept_here()
        read = build_read_top_ten(
            session, settings=settings, clock=FixedClock(at=now), orders=orders
        )
        her = await _id_of(session, THE_POPULATED_PLAYER.email)
        pair = {await _id_of(session, one.email) for one in SQUASH_PAIR.members}
        trophy = await build_read_home_ranking(
            session, clock=FixedClock(at=now), orders=orders
        ).execute(her)
        if trophy is None:
            raise TopTenIsWrong("her Home has no trophy, so Top 10 has no sport")
        opening = await read.execute(her, trophy.sport, falls_through=True)
        top = await read.execute(her, RANKED_SPORT)
        paired = await read.execute(her, PAIRED_SPORT)
        empty = await read.execute(her, EMPTY_SPORT)
        crowd = {
            await _id_of(session, member.email): member
            for member in RANKING_CROWD.members
        }
        walker = next((row for row in top.rows if row.place == WALKED_AT), None)
        theirs = (
            None
            if walker is None or walker.player_id not in crowd
            else await read.execute(walker.player_id, RANKED_SPORT, falls_through=True)
        )
    where = "Top 10"
    if not opening.rows:
        raise TopTenIsWrong(
            f"{where}: her row should open on {trophy.sport.value.lower()}, or the "
            f"sport it falls through to, with cards, and reads {_line(opening)}"
        )
    placed = trophy.general_place
    if placed is not None and placed <= TOP_TEN:
        if opening.sport is not trophy.sport or not any(
            row.is_you for row in opening.rows
        ):
            raise TopTenIsWrong(
                f"{where}: she is {placed} in {trophy.sport.value.lower()}, so "
                f"her row should open there with her own card, and reads "
                f"{_line(opening)}"
            )
    if [row.place for row in top.rows] != list(range(1, TOP_TEN + 1)):
        raise TopTenIsWrong(
            f"{where} · {RANKED_SPORT.value.lower()}: places 1 to {TOP_TEN} are "
            f"promised, and it reads {_line(top)}"
        )
    if {row.player_id for row in paired.rows} != pair or len(paired.rows) != 2:
        raise TopTenIsWrong(
            f"{where} · {PAIRED_SPORT.value.lower()}: the pair alone is promised, "
            f"and it reads {_line(paired)}"
        )
    if empty.rows or not empty.anyone_listed:
        raise TopTenIsWrong(
            f"{where} · {EMPTY_SPORT.value.lower()}: nobody listed there and "
            f"somebody elsewhere is promised, and it reads {_line(empty)}"
        )
    if (
        walker is None
        or theirs is None
        or [(row.place, row.is_you) for row in theirs.rows if row.is_you]
        != [(WALKED_AT, True)]
    ):
        raise TopTenIsWrong(
            f"{where} · {RANKED_SPORT.value.lower()}: the crowd player placed "
            f"{WALKED_AT} should read their own card there, and it reads "
            f"{_line(top) if theirs is None else _line(theirs)}"
        )
    return (
        f"Top 10: opens on {_line(opening)}; {_line(top)}; {_line(paired)}; "
        f"{_line(empty)} · ten with your own card: sign in as "
        f"{crowd[walker.player_id].email} ({WALKED_AT}th in "
        f"{RANKED_SPORT.value.lower()})"
    )


def _line(top: TopTen) -> str:
    if not top.rows:
        return f"{top.sport.value.lower()} · nobody listed"
    cards = ", ".join(
        f"{row.place} {'you' if row.is_you else row.nickname}" for row in top.rows
    )
    return f"{top.sport.value.lower()} · {cards}"


def squash_pair_lines(seeded: SeededSquashPair) -> list[str]:
    """The report's section: the pair, their group and their games."""

    state = "created" if seeded.created else "already there"
    lines = [
        f"Top 10's squash pair ({SQUASH_GROUP} at {SQUASH_CLUB.name}, {state}):",
        *(f"  {member.nickname} <{member.email}>" for member in SQUASH_PAIR.members),
    ]
    for game in seeded.games:
        made = "booked" if game.made else "already booked"
        acts = ", ".join(game.acts) or "nothing owed"
        start = game.start.astimezone(CLUB_ZONE)
        lines.append(f"  {start:%a %d %b %H:%M} · {made} · {acts}")
    return lines


async def _id_of(session: AsyncSession, email: str) -> UUID:
    user = await build_user_repository(session).get_by_email(email)
    if user is None:
        raise RuntimeError(f"{email} is not registered — the accounts run first")
    return user.id
