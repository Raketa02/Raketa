"""Her For-fun deck, a card in every band of the Social vibe (#832;
``docs/adr/0207`` §2, §8, §11; PRD #827's story 94).

**Her For-fun deck is a tennis one.** Her padel intent is competitive and her
tennis intent For fun, so the deck the For-fun cards are walked on is tennis:
singles, where a card's Social vibe is the plain overlap of two players — twice
the tags they share over all the tags the two carry. **The cohort can't promise
the four bands**: six of its members want For-fun tennis, and what each shares
with her is the draw's. So this layer writes **four players of its own, outside
the cohort** (:data:`FOR_FUN_CROWD`), as the ranking's crowd and the squash pair
are — one for each band the player app draws, each holding tags chosen against
hers (``catalog.HER_TAGS``), ADR-0207 §7's eight among them and the last holding
the eight a player may. Each row names its band, and **the band is checked on
import**, through the vibe Proposals itself works out, so a row can't promise a
band its tags don't reach.

- **At the Level she started tennis on**: rated by sitting her questionnaire's
  answers, so the four stand level with each other and well inside For fun's
  window of her, wherever her evenings have moved her since — and among the
  four only the company tells two tables apart.
- **Settled**: committed sixty days ago, out of New in Rakieta's month and the
  newcomer's fourteen days, at her week's hours, For fun in tennis alone, a card
  each.
- **In** *Tenis na luzie* **at Prądnik Tennis**, her group, which sells tennis on
  her evenings and her Saturday morning — opened and joined **thirty-one days
  ago**, so nobody in it is *new* to it and Hottest groups reads it untagged,
  never GROWING over the groups that row's claims are about.

**The proposer deals it**, for this one pool, at the run's instant, after every
layer that books her an hour — so nothing that run books takes an hour off a
card dealt here — and **after the outbox is drained**, since the proposer reads
everybody's tags off the directory only a delivery writes. Nothing here chooses
who is on a card: five people make ten pairs, and the courts at her week's hours
deal every one of them within the fortnight's first days, the best company first.

**On a later run the deck is read as it stands.** The proposals layer deals
every pool, this one included, before her bookings; a card an earlier run dealt
keeps its pair whatever that run books; and a later day's game on the day can
fill her two games a week. So a card can be withheld from her deck there, and
its pair is never dealt again while it lasts: ``assert_the_for_fun_deck`` holds
every band on the run that opens the group and reports a band missing after it
as a cost — a fresh store draws all four.

**The bands are the player app's** (ADR-0207 §8: the backend sends only the %),
so :data:`BANDS` is a copy of §8's table, the one this fixture is read by. A
tuning of the thresholds in the app moves the table there first, and this copy
after it.

**Re-running writes nothing twice**: the people are found by address, the group
is hers of that name at that club, joining again records nothing, and the
proposer deals no pair already on a card. A run on a later day deals later
hours, the earlier cards expiring at their own book-by.

``assert_the_for_fun_deck`` reads her For-fun tennis deck in the group through
its own use case among the screens.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_group_code_minter,
    build_home_clubs,
    build_propose_games,
    build_read_group_deck,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.groups.application.commands import CreatePlayerGroupCommand
from app.modules.groups.application.create_player_group import CreatePlayerGroup
from app.modules.groups.domain.value_objects import GroupName, JoinPolicy
from app.modules.player_profile.domain.social_tags import SocialTag
from app.modules.proposals.application.commands import ReadGroupDeckCommand
from app.modules.proposals.application.propose_games import Proposed
from app.modules.proposals.domain.vibe import social_vibe_of
from app.seeds.bookings import club_id_of
from app.seeds.catalog import (
    CATALOG_SURNAMES,
    CENTRE,
    COHORT_SURNAMES,
    HER_TAGS,
    MIDDLING,
    PROTAGONIST_WEEK,
    THE_POPULATED_PLAYER,
    dealt_nickname,
)
from app.seeds.clock import FixedClock
from app.seeds.clubs import SEED_CLUBS
from app.seeds.cohort import CLUB_PLAYER, COHORT, COHORT_SEED, Cohort, CohortMember
from app.seeds.groups import group_repository, group_run_by, join_group
from app.seeds.money import THE_FAKE, SeedMoney
from app.seeds.new_in_rakieta import JOINER_SURNAMES, JOINERS
from app.seeds.ranking_crowd import CROWD_SURNAMES, RANKING_CROWD
from app.seeds.rooms import deliver_everything_told
from app.seeds.top_ten import SQUASH_PAIR, SQUASH_SURNAMES

#: Her For-fun sport and the kind: tennis, For fun — her own intent there.
FOR_FUN_SPORT: Final = Sport.TENNIS
FOR_FUN_KIND: Final = SearchMode.FOR_FUN
#: Where they play: three tennis courts on her evenings and Saturday morning.
FOR_FUN_CLUB: Final = next(club for club in SEED_CLUBS if club.name == "Prądnik Tennis")
#: Her group there.
FOR_FUN_GROUP: Final = "Tenis na luzie"
GroupName(FOR_FUN_GROUP)

#: The players' second halves — disjoint from every other pool, so no handle
#: here is one already dealt.
FOR_FUN_SURNAMES: Final[tuple[str, ...]] = ("Ibarra",)

#: Committed this long before the run: out of New in Rakieta's 30 days and the
#: newcomer's 14.
_COMMITTED_DAYS_AGO: Final = 60
#: How long ago the group was opened and joined: past the 30 days a member
#: counts as new to it on Hottest groups.
OPENED_AGO: Final = timedelta(days=31)


@final
@dataclass(frozen=True, slots=True)
class Band:
    """One of the player app's Social vibe bands: its word and the lowest %
    it holds."""

    word: str
    lowest: int


#: **The app's bands, highest first** — ``docs/adr/0207`` §8's table, copied:
#: the backend sends only the %, and this is how the fixture reads its cards.
BANDS: Final[tuple[Band, ...]] = (
    Band("Great vibe", 70),
    Band("Good vibe", 45),
    Band("Some common ground", 20),
    Band("Fresh mix", 0),
)


def band_of(pct: int) -> Band:
    """The band a card's % is drawn in."""

    return next(band for band in BANDS if pct >= band.lowest)


#: **One player per band, and the tags that put them there**, against her six.
#: Singles, so the vibe is twice the tags shared over all the tags carried.
_ROWS: Final[tuple[tuple[str, tuple[SocialTag, ...]], ...]] = (
    # Five of hers and a coffee: 10 of 12, 83%.
    (
        "Great vibe",
        (
            SocialTag.PLAYS_TO_WIN,
            SocialTag.HERE_TO_IMPROVE,
            SocialTag.WARMS_UP_PROPERLY,
            SocialTag.HAPPY_TO_SHARE_TIPS,
            SocialTag.HAPPY_TO_SWAP_PARTNERS,
            SocialTag.STAYS_FOR_A_COFFEE,
        ),
    ),
    # Three of hers and a bite after: 6 of 10, 60%.
    (
        "Good vibe",
        (
            SocialTag.WARMS_UP_PROPERLY,
            SocialTag.GENEROUS_ON_LINE_CALLS,
            SocialTag.HAPPY_TO_SWAP_PARTNERS,
            SocialTag.UP_FOR_A_BITE_AFTER,
        ),
    ),
    # Two of hers among five: 4 of 11, 36%.
    (
        "Some common ground",
        (
            SocialTag.HERE_TO_IMPROVE,
            SocialTag.HAPPY_TO_SHARE_TIPS,
            SocialTag.NEW_IN_TOWN,
            SocialTag.KEEPS_IN_TOUCH,
            SocialTag.BRINGS_THE_ENERGY,
        ),
    ),
    # One of hers among the eight a player may hold: 2 of 14, 14%.
    (
        "Fresh mix",
        (
            SocialTag.PLAYS_TO_WIN,
            SocialTag.STAYS_FOR_A_DRINK,
            SocialTag.STAYS_FOR_A_COFFEE,
            SocialTag.UP_FOR_A_BITE_AFTER,
            SocialTag.KEEPS_IN_TOUCH,
            SocialTag.LAUGHS_OFF_MISTAKES,
            SocialTag.PATIENT_WITH_BEGINNERS,
            SocialTag.HERE_TO_MEET_PLAYERS,
        ),
    ),
)


def _member(index: int, tags: tuple[SocialTag, ...]) -> CohortMember:
    return CohortMember(
        handle=f"for-fun-{index:02d}",
        ring="for-fun",
        archetype=CLUB_PLAYER.name,
        latitude=CENTRE.latitude,
        longitude=CENTRE.longitude,
        slots=tuple(f"{day}:{hour}" for day, hour in PROTAGONIST_WEEK),
        tags=tuple(tag.value for tag in tags),
        intents=((FOR_FUN_SPORT.value, "FOR_FUN"),),
        gender="MAN" if index % 2 else "WOMAN",
        gender_preference="ANY",
        committed_days_ago=_COMMITTED_DAYS_AGO,
        claims=MIDDLING.claims,
        demonstrations=MIDDLING.demonstrations,
        claim_spread=0,
        demonstration_spread=0,
        photograph=None,
        nickname=dealt_nickname(index, FOR_FUN_SURNAMES),
        intro=None,
    )


#: The four, in the shape ``seed_the_cohort`` writes — **not the cohort**: every
#: row above is declared.
FOR_FUN_CROWD: Final = Cohort(
    seed=COHORT_SEED,
    members=tuple(_member(index, tags) for index, (_, tags) in enumerate(_ROWS)),
    centre=COHORT.centre,
)
#: Each player's handle, by the band their row promises.
IN_THE_BAND: Final[dict[str, str]] = {
    member.handle: word
    for member, (word, _) in zip(FOR_FUN_CROWD.members, _ROWS, strict=True)
}


def vibe_with_her(member: CohortMember) -> int:
    """Their singles card's Social vibe with her, as the deck works it out."""

    her, them = UUID(int=0), UUID(int=1)
    pct = social_vibe_of(
        (her, them),
        {
            her: [SocialTag(tag) for tag in HER_TAGS],
            them: [SocialTag(tag) for tag in member.tags],
        },
    )
    if pct is None:
        raise RuntimeError(f"'{member.handle}' and she share no table")
    return pct


def _refuse_a_crowd_that_misses_a_band() -> None:
    """On import: every band one row, each row inside the band it names, and
    no nickname or surname another pool deals."""

    if [word for word, _ in _ROWS] != [band.word for band in BANDS]:
        raise RuntimeError("the For-fun crowd holds one row per band, in order")
    for member in FOR_FUN_CROWD.members:
        pct = vibe_with_her(member)
        if band_of(pct).word != IN_THE_BAND[member.handle]:
            raise RuntimeError(
                f"'{member.handle}' shares {pct}% with her, a "
                f"{band_of(pct).word} card, and their row promises "
                f"{IN_THE_BAND[member.handle]}"
            )
    pools = (
        CATALOG_SURNAMES,
        COHORT_SURNAMES,
        CROWD_SURNAMES,
        JOINER_SURNAMES,
        SQUASH_SURNAMES,
    )
    if any(set(FOR_FUN_SURNAMES) & set(pool) for pool in pools):
        raise RuntimeError("the For-fun crowd's surnames are another pool's")
    taken = {
        member.nickname
        for member in (
            *COHORT.members,
            *RANKING_CROWD.members,
            *JOINERS.members,
            *SQUASH_PAIR.members,
        )
    }
    for member in FOR_FUN_CROWD.members:
        if member.nickname in taken:
            raise RuntimeError(f"'{member.nickname}' is already dealt")


_refuse_a_crowd_that_misses_a_band()


@final
@dataclass(frozen=True, slots=True)
class SeededForFun:
    group_id: UUID
    #: Whether this run opened the group, or found it already there.
    created: bool
    #: What the proposer dealt in it this run.
    proposed: Proposed


async def write_the_for_fun_deck(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    money: SeedMoney = THE_FAKE,
) -> SeededForFun:
    """Her group, the four in it, and the proposer over it — **after the four
    themselves, the clubs' courts and every layer that books her an hour**,
    which it reads and never writes. Drained by the layer itself, before the
    deal and after it."""

    opened = instant(now - OPENED_AGO)
    async with session_factory() as session:
        her = await _id_of(session, THE_POPULATED_PLAYER.email)
        crowd = [
            await _id_of(session, member.email) for member in FOR_FUN_CROWD.members
        ]
        club_id = await club_id_of(session, FOR_FUN_CLUB)
        group_id = await group_run_by(session, her, club_id=club_id, name=FOR_FUN_GROUP)
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
                    creator_id=her,
                    name=FOR_FUN_GROUP,
                    home_club_id=club_id,
                    join_policy=JoinPolicy.ANYONE,
                )
            )
        for player in crowd:
            await join_group(
                session,
                settings,
                group_id,
                player,
                FixedClock(at=instant(opened + timedelta(minutes=30))),
            )
    # **Drained before the deal**: the proposer reads everybody's tags off the
    # directory, which only a delivery writes — undrained, it would build by
    # nobody's tags.
    await deliver_everything_told(session_factory, money=money)
    async with session_factory() as session:
        proposed = await build_propose_games(session, clock=FixedClock(at=now)).execute(
            group_id
        )
    await deliver_everything_told(session_factory, money=money)
    return SeededForFun(group_id=group_id, created=created, proposed=proposed)


async def assert_the_for_fun_deck(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    seeded: SeededForFun,
) -> str:
    """*Her For-fun deck shows a card in every band* — read through
    ``ReadGroupDeck``, the Games tab's own read, filters and all, as her, in
    her group, tennis, For fun. The screen line.

    **Held on the run that opened the group**, whose deal came after every
    booking it made: a band with no card fails it by name with every card's %.
    **A later run reads what its store holds**, as Hottest groups' and New in
    Rakieta's claims do: a card an earlier run dealt keeps its pair, and a game
    this run booked her at its hour — or a second game this week, which fills
    her two — withholds it, so a band missing then is a cost on the line, and
    a fresh store draws all four."""

    async with session_factory() as session:
        her = await _id_of(session, THE_POPULATED_PLAYER.email)
        club_id = await club_id_of(session, FOR_FUN_CLUB)
        group_id = await group_run_by(session, her, club_id=club_id, name=FOR_FUN_GROUP)
        if group_id is None:
            raise RuntimeError(
                f"{THE_POPULATED_PLAYER.slug} has no {FOR_FUN_GROUP} to read — the "
                "For-fun layer runs first"
            )
        deck = await build_read_group_deck(
            session, settings=settings, clock=FixedClock(at=now)
        ).execute(
            ReadGroupDeckCommand(
                player_id=her, pool_id=group_id, sport=FOR_FUN_SPORT, kind=FOR_FUN_KIND
            )
        )
    where = (
        f"For-fun deck · {THE_POPULATED_PLAYER.slug} · {FOR_FUN_GROUP} · "
        f"{FOR_FUN_SPORT.value.lower()} for fun"
    )
    shown = [card.vibe for card in deck.cards if card.vibe is not None]
    drawn = {band_of(pct).word for pct in shown}
    missing = [band.word for band in BANDS if band.word not in drawn]
    if missing and seeded.created:
        raise RuntimeError(
            f"{where} draws no {', '.join(missing)} card: "
            f"{len(deck.cards)} card(s) at {', '.join(f'{pct}%' for pct in shown)}"
        )
    line = f"{where}: {len(deck.cards)} card(s) — " + ", ".join(
        f"{band_of(pct).word} {pct}%" for pct in shown
    )
    if missing:
        line += (
            f" (no {', '.join(missing)} card: an earlier run's, withheld by a game "
            "booked since — a fresh store draws every band)"
        )
    return line


def for_fun_lines(seeded: SeededForFun) -> list[str]:
    lines = [
        "For fun (#832):",
        f"  {FOR_FUN_GROUP} at {FOR_FUN_CLUB.name} — her For-fun tennis deck, a "
        "card in every Social vibe band "
        f"({'created' if seeded.created else 'already there'}, "
        f"{seeded.proposed.made} card(s) dealt this run)",
    ]
    for member in FOR_FUN_CROWD.members:
        lines.append(
            f"  {IN_THE_BAND[member.handle]} · {vibe_with_her(member)}% · "
            f"{member.nickname} <{member.email}>"
        )
    return lines


async def _id_of(session: AsyncSession, email: str) -> UUID:
    user = await build_user_repository(session).get_by_email(email)
    if user is None:
        raise RuntimeError(f"{email} is not registered — the accounts run first")
    return user.id
