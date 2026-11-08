"""The ranking's seed: a padel General list longer than its first page with
her below it, a beginner short of it, and a sport nobody is listed in (#768,
#770; ``docs/adr/0203``).

**Every result is a past booked game, on the path the product makes games on**
(``booked_history.py``): the runner hands ``RANKING_GAMES`` in beside the
cohort's own, so each is made, filled by its last yes, played, scored and
accepted through the use cases a phone runs. The agreement's delivery moves the
four Levels, and each move folds its player's row — **nothing here writes a
ranking row**, and the outbox drain the rooms layer runs is what fills them.

**Who, and why them.** Sixty-two are listed in padel — her, thirteen of the
cohort and **the ranking's crowd**, forty-eight players above all of them who
play only among themselves (``ranking_crowd.py``) — and ``cohort-a-12`` is the
beginner, three results short of the five. Every one of the cohort's:

- **holds no named role in a record fixture**: ``cohort-a-05``, ``-a-06`` and
  ``-a-07`` stay named nowhere, and ``-a-13``, ``-a-14`` and ``-a-16`` keep the
  counts their cards are built on (``cohort.py``'s ``PLAYED_GAMES``);
- **holds no claim a moved Level could break**: the named accounts other than
  her promise a position inside their band on every run, and ``the-one-sport-
  player`` and ``the-blank-week-player`` sit too close to its edges to play;
  the Advanced players stay out, because the histogram promises at least two;
- **fits everybody they play with**: every Level here is within the
  competitive window of every other (2,98–3,38 before the first game), every
  gender preference is *anybody* — but ``cohort-a-09``'s *men only*, whose five
  games are all men — and nobody is a newcomer, so every game predates their
  commit by days.

**Her five are three wins and two losses**, so her Level stays inside the
quarter-to-three-quarters of Established her claim promises on every run, and
she sits mid-list among the cohort's — and **below General's first page**,
with the crowd above her: *You · 56th*, the jump button's case. The fill draws
who partners whom off the Levels before any game moved them, so a loss names
whoever the fill seats across the net from her.

**Each player plays at most one game a day**, so every row's form is ordered
by the instant, never by a uuid. **Badminton is played by nobody**, which is
the empty sport.

**Re-running writes nothing twice**: the history layer finds every game booked
already, and a fold of an unchanged stream is the row it was.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_general_orders_kept_here,
    build_read_general_page,
    build_read_ranking,
    build_user_repository,
)
from app.core.config import Settings
from app.kernel import Instant, Sport
from app.modules.rankings.domain.ranking import (
    GENERAL_ENTRY,
    LISTED_FOR,
    PAGE_SIZE,
    CardState,
)
from app.seeds.booked_history import MADE_AHEAD
from app.seeds.catalog import THE_POPULATED_PLAYER
from app.seeds.clock import FixedClock
from app.seeds.cohort import COHORT, PROTAGONIST_HANDLE, PlayedGame
from app.seeds.ranking_crowd import RANKING_CROWD_GAMES, RANKING_CROWD

#: The sport the list is seeded in, and the one nobody plays.
RANKED_SPORT: Final = Sport.PADEL
EMPTY_SPORT: Final = Sport.BADMINTON

#: The one short of the five: *3 of 5 games — 2 more competitive padel games
#: put you on the list*.
THE_BEGINNER: Final = "cohort-a-12"


def _game(days_ago: int, side_a: tuple[str, str], side_b: tuple[str, str], won_by: str):
    return PlayedGame(
        sport=RANKED_SPORT.value,
        played_days_ago=days_ago,
        side_a=side_a,
        side_b=side_b,
        won_by=won_by,
    )


#: The protagonist, as every ranked game names her.
HER: Final = PROTAGONIST_HANDLE

#: **The ranked games, oldest first.** ``won_by`` names the side of the first
#: player declared on it, as every declared game does: the fill draws who
#: partners whom. Her three wins name her; her two losses name somebody across
#: the net from her.
RANKING_GAMES: Final[tuple[PlayedGame, ...]] = (
    _game(36, (HER, "cohort-d-04"), ("cohort-d-07", "cohort-b-04"), "A"),
    _game(35, ("cohort-a-11", "cohort-d-08"), ("cohort-a-08", "cohort-b-01"), "A"),
    _game(34, ("cohort-d-05", "cohort-d-01"), ("cohort-b-04", "cohort-d-07"), "B"),
    _game(33, (HER, "cohort-a-08"), ("cohort-d-04", "cohort-d-05"), "B"),
    _game(32, ("cohort-d-08", "cohort-b-01"), ("cohort-a-11", "cohort-d-01"), "B"),
    _game(31, ("cohort-b-04", "cohort-d-07"), (HER, THE_BEGINNER), "A"),
    _game(30, ("cohort-d-04", "cohort-a-08"), ("cohort-d-08", THE_BEGINNER), "A"),
    _game(28, ("cohort-c-00", "cohort-d-05"), ("cohort-a-11", "cohort-b-04"), "B"),
    _game(27, (HER, "cohort-d-07"), ("cohort-c-00", "cohort-d-08"), "A"),
    _game(26, ("cohort-d-04", "cohort-a-11"), ("cohort-c-00", THE_BEGINNER), "B"),
    _game(25, ("cohort-a-08", "cohort-d-01"), ("cohort-d-07", "cohort-d-08"), "A"),
    _game(24, ("cohort-c-00", "cohort-b-01"), (HER, "cohort-d-04"), "A"),
    _game(22, ("cohort-c-01", "cohort-a-08"), ("cohort-c-00", "cohort-b-04"), "A"),
    _game(21, ("cohort-a-11", "cohort-e-01"), ("cohort-c-01", "cohort-d-05"), "A"),
    # ``cohort-a-09`` plays men only, so these five are all men.
    _game(20, ("cohort-a-09", "cohort-e-01"), ("cohort-c-01", "cohort-d-01"), "A"),
    _game(19, ("cohort-a-09", "cohort-c-01"), ("cohort-e-01", "cohort-b-01"), "B"),
    _game(18, ("cohort-a-09", "cohort-d-01"), ("cohort-e-01", "cohort-c-01"), "A"),
    _game(17, ("cohort-a-09", "cohort-d-05"), ("cohort-c-01", "cohort-e-01"), "B"),
    _game(16, ("cohort-a-09", "cohort-b-01"), ("cohort-d-01", "cohort-e-01"), "A"),
)

#: How many results each player the games seat has, counted off the games —
#: the cohort's and the crowd's.
RESULTS: Final[Counter[str]] = Counter(
    handle for game in (*RANKING_GAMES, *RANKING_CROWD_GAMES) for handle in game.players
)

#: Everybody the list holds: every player with five results or more.
THE_RANKED: Final[frozenset[str]] = frozenset(
    handle for handle, results in RESULTS.items() if results >= GENERAL_ENTRY
)


def _refuse_a_ranking_nobody_could_play() -> None:
    """The declarations against the population, **on import**, so a game that
    could not be written fails before a database is touched."""

    crowd = {member.handle: member for member in RANKING_CROWD.members}
    days: dict[str, set[int]] = {}
    for index, game in enumerate((*RANKING_GAMES, *RANKING_CROWD_GAMES)):
        if not (game.was_scored and game.entered and game.answered):
            raise RuntimeError(f"ranking game {index} is not a result with a winner")
        if game.played_days_ago >= LISTED_FOR.days:
            raise RuntimeError(f"ranking game {index} is older than the 90 days")
        for handle in game.players:
            committed = (
                THE_POPULATED_PLAYER.profile.committed_days_ago
                if handle == HER and THE_POPULATED_PLAYER.profile is not None
                else (crowd.get(handle) or COHORT.by_handle(handle)).committed_days_ago
            )
            if committed <= game.played_days_ago + MADE_AHEAD.days:
                raise RuntimeError(
                    f"ranking game {index} was made before '{handle}' committed "
                    f"their profile ({committed} day(s) ago)"
                )
            if game.played_days_ago in days.setdefault(handle, set()):
                raise RuntimeError(
                    f"'{handle}' plays twice on one day: a row's form is ordered on "
                    f"the instant, and two at once leave it to a uuid"
                )
            days[handle].add(game.played_days_ago)
    if HER not in THE_RANKED:
        raise RuntimeError(f"'{HER}' has {RESULTS[HER]} result(s) and is not listed")
    if len(THE_RANKED) <= PAGE_SIZE:
        raise RuntimeError(
            f"{len(THE_RANKED)} are listed, and General is to run past its first "
            f"page of {PAGE_SIZE}"
        )
    if set(crowd) & {handle for game in RANKING_GAMES for handle in game.players}:
        raise RuntimeError("the crowd plays among themselves alone")
    if not 2 <= RESULTS[THE_BEGINNER] < GENERAL_ENTRY:
        raise RuntimeError(
            f"'{THE_BEGINNER}' has {RESULTS[THE_BEGINNER]} result(s); the beginner "
            f"has 2–4"
        )


_refuse_a_ranking_nobody_could_play()


class RankingIsWrong(RuntimeError):
    """The list a tester signs in to read is not the one this layer promises."""


@final
@dataclass(frozen=True, slots=True)
class SeededRanking:
    #: Her place, and how many are listed.
    place: int
    of: int
    #: The beginner's results.
    beginner_results: int
    #: The places on the page around her — *You · 56th*'s page.
    around_her: tuple[int, ...]


async def assert_the_ranking(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
) -> str:
    """*Padel is a list longer than a page with her below the first, the
    beginner is short of it, and badminton is empty* — read through the page's
    own use cases, as her and as the beginner, after the outbox is drained.
    Any of it missing fails the run by name."""

    seeded = await read_the_ranking(session_factory, settings=settings, now=now)
    return (
        f"the ranking · {RANKED_SPORT.value.lower()}: {PROTAGONIST_HANDLE} "
        f"{seeded.place} of {seeded.of}, below the first page, her page "
        f"{seeded.around_her[0]}–{seeded.around_her[-1]}; {THE_BEGINNER} "
        f"{seeded.beginner_results} of {GENERAL_ENTRY}; "
        f"{EMPTY_SPORT.value.lower()}: nobody listed"
    )


async def read_the_ranking(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
) -> SeededRanking:
    async with session_factory() as session:
        orders = build_general_orders_kept_here()
        read = build_read_ranking(
            session, settings=settings, clock=FixedClock(at=now), orders=orders
        )
        pages = build_read_general_page(
            session, settings=settings, clock=FixedClock(at=now), orders=orders
        )
        her = await _id_of(session, THE_POPULATED_PLAYER.email)
        beginner = await _id_of(session, COHORT.by_handle(THE_BEGINNER).email)
        padel = await read.execute(her, RANKED_SPORT)
        around = await pages.execute(her, RANKED_SPORT, around_the_reader=True)
        short = (await read.execute(beginner, RANKED_SPORT)).card
        empty = await read.execute(her, EMPTY_SPORT)
    where = f"the ranking · {RANKED_SPORT.value.lower()}"
    if padel.card.state is not CardState.LISTED or padel.card.place is None:
        raise RankingIsWrong(f"{where}: {PROTAGONIST_HANDLE} reads {padel.card!r}")
    if padel.listed_count < len(THE_RANKED):
        raise RankingIsWrong(
            f"{where}: {padel.listed_count} listed, and {len(THE_RANKED)} are promised"
        )
    if padel.card.place <= PAGE_SIZE or padel.card.place == padel.listed_count:
        raise RankingIsWrong(
            f"{where}: {PROTAGONIST_HANDLE} is {padel.card.place} of "
            f"{padel.listed_count}, which is not below the first page and off "
            f"the bottom"
        )
    if not any(row.is_you for row in around.rows) or padel.next is None:
        raise RankingIsWrong(
            f"{where}: the page around {PROTAGONIST_HANDLE} doesn't hold her, or "
            f"the first page has no page after it"
        )
    if short.state is not CardState.NEEDS_RESULTS or not 2 <= short.results < (
        GENERAL_ENTRY
    ):
        raise RankingIsWrong(f"{where}: {THE_BEGINNER} reads {short!r}")
    if empty.listed_count or empty.rows:
        raise RankingIsWrong(
            f"the ranking · {EMPTY_SPORT.value.lower()}: {empty.listed_count} "
            f"listed, and nobody is promised"
        )
    return SeededRanking(
        place=padel.card.place,
        of=padel.listed_count,
        beginner_results=short.results,
        around_her=tuple(row.place for row in around.rows),
    )


async def _id_of(session: AsyncSession, email: str) -> UUID:
    user = await build_user_repository(session).get_by_email(email)
    if user is None:
        raise RuntimeError(f"{email} is not registered — the accounts run first")
    return user.id
