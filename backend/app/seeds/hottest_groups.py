"""Hottest groups: one HOTTEST group by construction, and her Join request
waiting on it (#792; the Home rows mechanics §5, §20).

**Why a group of its own.** Everything else the seed writes falls where its own
layer needs it, and none of it is sure to make the row: the played history is
placed before her week, her booked games and the rescues are still to come, so
on many days no group has played this week — and the busiest group by heat,
*Padel po pracy*, which her games layer filled on the run's instant, would be
**GROWING** with nobody **HOTTEST** (call 3). So this layer writes the one
group the row cannot do without: **Wieczorny Kazimierz**, at Kazimierz Padel,
*People I approve*, owned by the ranking's crowd's first player and joined by
twenty-three more of them ten days ago — each let in by the Owner, as a
request there is only let in — with **three games booked in it two, three and
four days ago**, inside the seven days whatever the weekday. **A day the club
sells nothing is stepped over**, a day further back: Kazimierz Padel sells no
Monday, so a run on a Wednesday, Thursday or Friday plays one game a day
earlier than four days ago. 3 × 24 new + 20 + 2 × 3 = 98 against *Padel po
pracy*'s 80.

**The crowd, because nobody deals them a game.** Their week is cleared
(``ranking_crowd.py``), so joining a group puts no card in anybody's deck, and
a game among four of them fills nobody's week but theirs. **The games are not
scored**: *games this week* counts a game scored or not (call 4), and a result
would move their Levels and her place among them, which the ranking's seed
promises. Each is made two days before its hour and filled by its four yeses
through the run's provider, the cut-off job run at its cut-off, as the played
history's are.

**And her request, waiting on it**, so *Asked* and *Withdraw request* can be
walked: she taps *Ask to join* an hour before the run. A request she withdrew
in the app is put back on the next run — asking again is what withdrawing
allows — and one she was let into stays a membership.

**The rest of the row is the other layers'.** *Padel po pracy* is **GROWING**
(everybody in it joined on the run's instant); the groups the history and the
groups layer made weeks ago are **untagged**; and *Błonia po pracy*, two
players, **stays out**. ``assert_the_hottest_groups`` reads her row through its
own use case, among the screens, and fails the run by name unless all of that
is what she reads.

**Re-running writes nothing twice**: the group is the Owner's of that name at
that club, a member joining or let in again records nothing, a game is looked
for by its four in the group's pool **this week** — so a run days later, which
finds the last run's games past the seven days, books the four again where
they now fall, as the played history places a fresh game only where none was
written — and a request asked again while it waits records nothing. **Only a
fresh store's run is held to the whole row**: the GROWING and untagged cards
are the other layers' groups, and those age with the store (in thirty days
nobody in them is new), so a later run reports them and fails on this layer's
own promises alone.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Final, TypeVar, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_court_hours,
    build_group_administrators,
    build_group_born_games,
    build_group_code_minter,
    build_group_directory,
    build_group_faces,
    build_home_clubs,
    build_member_relations,
    build_player_bookings,
    build_rated_group_members,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.clubs.domain.court_hours import CLUB_ZONE, hour_start, local_day
from app.modules.groups.application.answer_join_request import ApproveJoinRequest
from app.modules.groups.application.commands import (
    AnswerJoinRequestCommand,
    CreatePlayerGroupCommand,
)
from app.modules.groups.application.create_player_group import CreatePlayerGroup
from app.modules.groups.application.hottest_groups import (
    HottestGroupCard,
    HottestGroupsRow,
    ReadHottestGroups,
    ReadHottestGroupsPage,
)
from app.modules.groups.domain.hottest import (
    CARDS,
    COUNTED_UP_TO,
    GAMES_WINDOW,
    HeatTag,
)
from app.modules.groups.domain.value_objects import GroupRelation, JoinPolicy
from app.modules.proposals.domain.deck import GAME_LENGTH
from app.seeds.booked_history import MADE_AHEAD
from app.seeds.bookings import all_say_yes, club_id_of, the_cut_off_came
from app.seeds.catalog import THE_POPULATED_PLAYER
from app.seeds.clock import FixedClock, days_before, hours_before
from app.seeds.clubs import SEED_CLUBS
from app.seeds.groups import group_repository, group_run_by, join_group
from app.seeds.money import THE_FAKE, SeedMoney
from app.seeds.rooms import deliver_everything_told

#: The group the row cannot do without.
HOTTEST_GROUP: Final = "Wieczorny Kazimierz"
HOTTEST_CLUB: Final = next(
    club for club in SEED_CLUBS if club.name == "Kazimierz Padel"
)
#: The Owner and twenty-three members, from the ranking's crowd.
MEMBERS: Final = 24
#: Created, and every member let in, this long before the run — inside the 30
#: days, so all of them are new this month.
OPENED_DAYS_AGO: Final = 10
#: Games in it this week, each a different four on a day of its own.
GAMES: Final = 3
#: The latest a game is played: this many days before the run, walking back a
#: day at a time to the edge of the 7 days past a day the club sells nothing —
#: Kazimierz Padel's Mondays, a closed day — so two, three and four days ago, or
#: one more back, whatever the weekday.
FIRST_GAME_DAYS_AGO: Final = 2
#: Her request, asked this long before the run.
ASKED_HOURS_AGO: Final = 1
#: The two-player group the other layers leave, which the row leaves out.
TOO_SMALL: Final = "Błonia po pracy"
#: Her own group, which the games layer filled on the run's instant.
GROWING_GROUP: Final = "Padel po pracy"


class HottestGroupsRefused(RuntimeError):
    """The seed cannot write, or she does not read, what the row needs."""


@final
@dataclass(frozen=True, slots=True)
class SeededHottestGroups:
    group_id: UUID
    #: Whether this run created the group, or found it already there.
    created: bool
    #: The hours of its games, and whether this run booked each.
    games: tuple[tuple[Instant, bool], ...]


async def write_the_hottest_groups(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    crowd: Sequence[tuple[str, UUID]],
    money: SeedMoney = THE_FAKE,
) -> SeededHottestGroups:
    """The group, its members, its games and her request — **after the friends
    layers and before the screens**, and after the cards, the clubs' courts and
    the ranking's crowd, which it reads and never writes. Drained by the layer
    itself."""

    if len(crowd) < MEMBERS:
        raise HottestGroupsRefused(
            f"{HOTTEST_GROUP} needs {MEMBERS} of the ranking's crowd, and there "
            f"are {len(crowd)}"
        )
    owner, *members = [player_id for _, player_id in crowd[:MEMBERS]]
    opened = instant(now - timedelta(days=OPENED_DAYS_AGO))
    async with session_factory() as session:
        club_id = await club_id_of(session, HOTTEST_CLUB)
        group_id = await group_run_by(
            session, owner, club_id=club_id, name=HOTTEST_GROUP
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
                    name=HOTTEST_GROUP,
                    home_club_id=club_id,
                    join_policy=JoinPolicy.PEOPLE_I_APPROVE,
                )
            )
        for minute, member in enumerate(members, start=1):
            clock = FixedClock(at=instant(opened + timedelta(minutes=minute)))
            await join_group(session, settings, group_id, member, clock)
            await ApproveJoinRequest(
                groups=group_repository(session),
                uow=build_unit_of_work(session),
                clock=clock,
            ).execute(
                AnswerJoinRequestCommand(
                    group_id=group_id, player_id=member, answered_by=owner
                )
            )

        games: list[tuple[Instant, bool]] = []
        hours: list[tuple[Instant, Instant]] | None = None
        for index in range(GAMES):
            four = tuple(members[4 * index : 4 * index + 4])
            played = await _played_this_week(session, group_id, four, now=now)
            if played is not None:
                games.append((played, False))
                continue
            if hours is None:
                hours = await _the_game_hours(session, club_id, now=now)
            start, made_at = hours[index]
            answer = await all_say_yes(
                session,
                settings=settings,
                clock=FixedClock(at=made_at),
                provider=money.provider(),
                pool_id=group_id,
                club_id=club_id,
                start=start,
                players=four,
                sport=Sport.PADEL,
                kind=SearchMode.COMPETITIVE,
            )
            if answer is None or answer.booked is None:
                raise HottestGroupsRefused(
                    f"{HOTTEST_GROUP}'s game at "
                    f"{start.astimezone(CLUB_ZONE):%a %d %b %H:%M} filled and did "
                    f"not book: {answer!r}"
                )
            booked = await build_player_bookings(session).find(answer.booked.booking_id)
            if booked is not None and made_at < booked.cut_off:
                await the_cut_off_came(session, settings=settings, at=booked.cut_off)
            games.append((start, True))

        her = await _her_id(session)
        await join_group(
            session, settings, group_id, her, hours_before(now, ASKED_HOURS_AGO)
        )
    await deliver_everything_told(session_factory, money=money)
    return SeededHottestGroups(
        group_id=group_id, created=created, games=tuple(sorted(games))
    )


async def assert_the_hottest_groups(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    seeded: SeededHottestGroups,
) -> str:
    """Her *Hottest groups*, read through its own use case: **one HOTTEST — this
    layer's group, with her request waiting on it — at least one GROWING and
    one untagged card, and the two-player group out**, or the run fails by
    name — and *Groups heating up*, page after page, through its own (#813):
    **the row its first six, and the row's total and the first page's what it
    lists**, capped. The screen line."""

    async with session_factory() as session:
        her = await _her_id(session)
        row = await _built(
            ReadHottestGroups, session, settings=settings, now=now
        ).execute(her)
        first_total, listed = await _every_page(
            _built(ReadHottestGroupsPage, session, settings=settings, now=now), her
        )
    _refuse_a_row_that_lies(row.cards, seeded, whole_row=seeded.created)
    _refuse_a_page_that_disagrees(row, first_total=first_total, listed=listed)
    return (
        f"Hottest groups ({row.total}, {len(listed)} on Groups heating up): "
        + " · ".join(_card_line(card) for card in row.cards)
    )


_Read = TypeVar("_Read", ReadHottestGroups, ReadHottestGroupsPage)


def _built(
    read: type[_Read], session: AsyncSession, *, settings: Settings, now: Instant
) -> _Read:
    return read(
        directory=build_group_directory(session),
        games=build_group_born_games(session),
        clubs=build_home_clubs(session),
        ratings=build_rated_group_members(session),
        faces=build_group_faces(session, settings=settings),
        relations=build_member_relations(session),
        administrators=build_group_administrators(session),
        clock=FixedClock(at=now),
    )


async def _every_page(
    read: ReadHottestGroupsPage, her: UUID
) -> tuple[int | None, list[HottestGroupCard]]:
    """*Groups heating up*, page after page: the first page's total, and every
    card on them."""

    page = await read.execute(her, after=None)
    first_total, listed = page.total, list(page.cards)
    while page.next is not None:
        page = await read.execute(her, after=page.next)
        listed.extend(page.cards)
    return first_total, listed


def _refuse_a_page_that_disagrees(
    row: HottestGroupsRow,
    *,
    first_total: int | None,
    listed: Sequence[HottestGroupCard],
) -> None:
    """The row is the page's first six, and both count what the page lists."""

    def placed(cards: Sequence[HottestGroupCard]) -> list[tuple[UUID, HeatTag | None]]:
        return [(card.group.row.id, card.tag) for card in cards]

    if placed(row.cards) != placed(listed[:CARDS]):
        raise HottestGroupsRefused(
            f"her Hottest groups should be the first {CARDS} of Groups heating "
            f"up, and read {[_card_line(card) for card in row.cards]} against "
            f"{[_card_line(card) for card in listed[:CARDS]]}"
        )
    if not row.total == first_total == min(len(listed), COUNTED_UP_TO):
        raise HottestGroupsRefused(
            f"her Hottest groups line counts {row.total}, the page's first "
            f"{first_total}, and Groups heating up lists {len(listed)}"
        )


def _refuse_a_row_that_lies(
    row: Sequence[HottestGroupCard], seeded: SeededHottestGroups, *, whole_row: bool
) -> None:
    hottest = [card for card in row if card.tag is HeatTag.HOTTEST]
    if [card.group.row.id for card in hottest] != [seeded.group_id]:
        raise HottestGroupsRefused(
            f"her Hottest groups should open on {HOTTEST_GROUP}, HOTTEST, and "
            f"read: {[_card_line(card) for card in row]}"
        )
    if hottest[0].group.relation is not GroupRelation.REQUESTED:
        raise HottestGroupsRefused(
            f"her request on {HOTTEST_GROUP} should be waiting, and it reads "
            f"{hottest[0].group.relation.value}"
        )
    if any(card.group.row.name == TOO_SMALL for card in row):
        raise HottestGroupsRefused(
            f"{TOO_SMALL} has two players and should be left out of the row"
        )
    if not whole_row:
        return
    if not any(card.tag is HeatTag.GROWING for card in row):
        raise HottestGroupsRefused(
            f"her Hottest groups should carry a GROWING card ({GROWING_GROUP}), "
            f"and read: {[_card_line(card) for card in row]}"
        )
    if not any(card.tag is None for card in row):
        raise HottestGroupsRefused(
            "her Hottest groups should carry an untagged card, and read: "
            f"{[_card_line(card) for card in row]}"
        )


def _card_line(card: HottestGroupCard) -> str:
    tag = "" if card.tag is None else f" {card.tag.value}"
    return (
        f"{card.group.row.name}{tag} ({card.games_this_week} games, "
        f"{card.group.row.member_count} players, +{card.new_this_month}, "
        f"{card.group.relation.value.lower()})"
    )


def hottest_group_lines(seeded: SeededHottestGroups) -> list[str]:
    """The report's section."""

    state = "created" if seeded.created else "already there"
    lines = [
        f"Hottest groups — {HOTTEST_GROUP} at {HOTTEST_CLUB.name}, People I "
        f"approve, {MEMBERS} of the ranking's crowd · {state}; her request waits "
        f"on it:"
    ]
    lines.extend(
        f"  {start.astimezone(CLUB_ZONE):%a %d %b %H:%M} · "
        f"{'booked' if made else 'already booked'} · not scored"
        for start, made in seeded.games
    )
    return lines


async def _the_game_hours(
    session: AsyncSession, club_id: UUID, *, now: Instant
) -> list[tuple[Instant, Instant]]:
    """An hour for each game, latest first: one on each of the club's last days
    to sell before the run, from ``FIRST_GAME_DAYS_AGO`` back to the edge of the
    seven days, stepping over a day it sold nothing. The hour, and when it was
    made."""

    hours: list[tuple[Instant, Instant]] = []
    for days_ago in range(FIRST_GAME_DAYS_AGO, GAMES_WINDOW.days):
        hour = await _a_padel_hour(session, club_id, days_ago=days_ago, now=now)
        if hour is not None:
            hours.append(hour)
        if len(hours) == GAMES:
            return hours
    raise HottestGroupsRefused(
        f"{HOTTEST_CLUB.name} sold a padel hour on {len(hours)} of the days "
        f"{FIRST_GAME_DAYS_AGO} to {GAMES_WINDOW.days - 1} before the run, and "
        f"{HOTTEST_GROUP} needs {GAMES} inside the seven days"
    )


async def _a_padel_hour(
    session: AsyncSession, club_id: UUID, *, days_ago: int, now: Instant
) -> tuple[Instant, Instant] | None:
    """The first padel hour the club sold on that day, made two days before it
    and over before the run — or ``None``, on a day it sold none. The hour, and
    when it was made."""

    day = local_day(days_before(now, days_ago).now())
    day_start = hour_start(day, 0)
    court_hours = build_court_hours(session)
    on_sale = await court_hours.on_sale(
        [club_id],
        start=day_start,
        end=instant(day_start + timedelta(days=1)),
        now=instant(day_start - MADE_AHEAD),
    )
    for start in sorted(
        hour.start
        for hour in on_sale
        if hour.sport is Sport.PADEL and hour.taking_new_cards
    ):
        made_at = instant(start - MADE_AHEAD)
        if start + GAME_LENGTH <= now and await court_hours.offered(
            club_id, sport=Sport.PADEL, start=start, now=made_at
        ):
            return start, made_at
    return None


async def _played_this_week(
    session: AsyncSession, group_id: UUID, four: tuple[UUID, ...], *, now: Instant
) -> Instant | None:
    """The hour of a game these four already have in the group **inside the
    seven days** — an earlier run's, on this day or a day or two before — or
    ``None``, when the last one has aged out of *games this week*."""

    since = instant(now - GAMES_WINDOW)
    for game in await build_player_bookings(session).of_player(four[0], since=since):
        if (
            game.pool_id == group_id
            and game.start <= now
            and {*game.first_side, *game.second_side} == set(four)
        ):
            return game.start
    return None


async def _her_id(session: AsyncSession) -> UUID:
    user = await build_user_repository(session).get_by_email(THE_POPULATED_PLAYER.email)
    if user is None:
        raise HottestGroupsRefused(
            f"{THE_POPULATED_PLAYER.slug} is not registered — the accounts layer "
            f"runs first"
        )
    return user.id
