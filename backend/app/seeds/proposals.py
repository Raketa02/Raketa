"""The games still filling: four picks for the protagonist, with nought, one,
two and three of the other three In (#538; the screens Part D).

**Through the use cases a game is made and answered by** (``docs/adr/0029``):
each pick is made by ``MakeProposal`` — the use case the engine will drive
(#540), which reads the court hour's share and book-by off the club and refuses
a version whose people do not fit — and each yes is said by ``SayYes``, the
use case the phone's swipe runs, so a seeded yes needed a saved card and a live
yes to spare exactly as a real one does. Nothing here opens a table.

**Its own group, because none of the others can seat a four.** Every Play
group above is drawn from the named accounts (``groups.py``), and the
protagonist's own padel group holds two accounts with no Player profile — who
fit nobody, since a gate that cannot be evaluated excludes. So this layer
gathers a crowd the way a group does: she creates *Padel po pracy* at Bonarka
Arena, which sells padel on her evenings and her Saturday, and **the cohort
members who fit her and each other** join it — chosen by the real pair rule
(``PlayerFit``), in the cohort's own order, so the group is a clique and any
three of it make a four with her.

**Each pick is at an hour she is free and the club sells**, one a day from two
days out, so a card outlives a day of developing against it; and each names
the members free for that whole hour, the ones no earlier pick named first, so
the four cards show different faces where the crowd allows.

**Written at the run's own now**, since a proposal is about an hour ahead; and
**re-running makes no pick twice** — a pick already filling in the group at an
hour is found and left as the developer left it. A later run on a later day
chooses later hours, and the earlier picks expire at their own book-by.

**The run fails by name** when the crowd cannot seat a pick with three In, rather
than seeding a deck that cannot show *Book it now*.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_club_account_repository,
    build_domain_event_store,
    build_event_publisher,
    build_group_code_minter,
    build_group_directory,
    build_home_clubs,
    build_make_proposal,
    build_player_fit,
    build_player_profile_repository,
    build_proposal_directory,
    build_proposal_guards,
    build_proposal_repository,
    build_sellable_court_hours,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport
from app.modules.clubs.domain.court_hours import CLUB_ZONE
from app.modules.groups.application.commands import CreatePlayerGroupCommand
from app.modules.groups.application.create_player_group import CreatePlayerGroup
from app.modules.groups.domain.value_objects import GroupName, JoinPolicy
from app.modules.player_profile.domain.ports import PlayerProfileRepository
from app.modules.player_profile.domain.weekly_hours import free_for_the_hour
from app.modules.proposals.application.answers import SayYes
from app.modules.proposals.application.commands import (
    AnswerProposalCommand,
    MakeProposalCommand,
)
from app.modules.proposals.domain.proposal import Origin
from app.modules.users.domain.value_objects import Email
from app.seeds.catalog import THE_POPULATED_PLAYER
from app.seeds.clock import FixedClock
from app.seeds.clubs import SEED_CLUBS, desk_email
from app.seeds.groups import group_repository, join_group

#: The group the games are dealt in, and where it plays.
GAMES_GROUP: Final = "Padel po pracy"
GAMES_CLUB: Final = next(club for club in SEED_CLUBS if club.name == "Bonarka Arena")
GAMES_SPORT: Final = Sport.PADEL
#: Her padel intent, so her deck's segment is the one these are dealt in.
GAMES_KIND: Final = SearchMode.COMPETITIVE

#: How many of the cohort the group gathers besides her: enough for four picks
#: of three different people each.
CROWD: Final = 12
#: The picks, by how many of the other three are In. The last is *Book it now*.
IN_ON_EACH: Final = (0, 1, 2, 3)
#: How far ahead the first pick is, so a card outlives a day of developing.
LEAD: Final = timedelta(days=2)
#: How far ahead a deck looks (the mechanics §4.3).
HORIZON: Final = timedelta(days=14)

# Refused on import, through the domain's own value object, as ``groups.py``'s
# names are: a name the New group form would refuse fails here rather than half
# way through a run.
GroupName(GAMES_GROUP)


@final
@dataclass(frozen=True, slots=True)
class SeededPick:
    proposal_id: UUID
    start: Instant
    #: The three named beside her, in the order they were named.
    named: tuple[UUID, ...]
    #: How many of them said yes.
    in_count: int
    #: Whether this run made it, or found it already filling.
    made: bool


@final
@dataclass(frozen=True, slots=True)
class SeededProposals:
    group_id: UUID
    created_group: bool
    #: How many of the cohort fit her and each other and are in the group.
    crowd: int
    picks: tuple[SeededPick, ...]


class NotEnoughToDeal(RuntimeError):
    """The crowd cannot seat the picks this layer promises."""


async def write_the_proposals(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    cohort: Sequence[tuple[str, UUID]],
) -> SeededProposals:
    """Gather the group, then make every pick not already filling in it and
    say its yeses.

    **After the accounts, the cohort, their cards and the clubs' courts**, which
    it reads and never writes, and after every layer that writes a block — the
    fit is read live, so a block written later could leave a four that no
    longer fits."""

    clock = FixedClock(at=now)
    async with session_factory() as session:
        her = await _protagonist(session)
        club_id = await _club_id(session)
        crowd = await _the_crowd(session, her, [player for _, player in cohort], now)
        group_id, created = await _the_group(
            session, settings, her, club_id, crowd, now
        )
        free = await _free_at(session, her, crowd, club_id, now)
        starts = tuple(free)[: len(IN_ON_EACH)]
        if len(starts) < len(IN_ON_EACH):
            raise NotEnoughToDeal(
                f"{GAMES_GROUP} cannot deal {len(IN_ON_EACH)} picks: {len(crowd)} of "
                f"the cohort fit her and each other, and only {len(starts)} days of "
                f"the fortnight have an hour {GAMES_CLUB.name} sells that she and "
                f"three of them are free for"
            )
        filling = await _filling_at(session, her, group_id, now)
        picks: list[SeededPick] = []
        used: set[UUID] = set()
        for start, in_count in zip(starts, IN_ON_EACH, strict=True):
            if start in filling:
                proposal_id, named, said = filling[start]
                picks.append(SeededPick(proposal_id, start, named, said, made=False))
                used.update(named)
                continue
            named = tuple(
                sorted(free[start], key=lambda member: member in used)[
                    : max(IN_ON_EACH)
                ]
            )
            used.update(named)
            proposal_id = await build_make_proposal(session, clock=clock).execute(
                MakeProposalCommand(
                    pool_id=group_id,
                    origin=Origin.PICK,
                    poster_id=None,
                    sport=GAMES_SPORT,
                    kind=GAMES_KIND,
                    club_id=club_id,
                    start=start,
                    versions=[(her, *named)],
                )
            )
            for player in named[:in_count]:
                await _says_yes(session, clock, proposal_id, player)
            picks.append(SeededPick(proposal_id, start, named, in_count, made=True))
    return SeededProposals(
        group_id=group_id, created_group=created, crowd=len(crowd), picks=tuple(picks)
    )


async def _protagonist(session: AsyncSession) -> UUID:
    user = await build_user_repository(session).get_by_email(THE_POPULATED_PLAYER.email)
    if user is None:
        raise RuntimeError("the protagonist is not registered — the accounts run first")
    return user.id


async def _club_id(session: AsyncSession) -> UUID:
    account = await build_club_account_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).get_by_email(Email(desk_email(GAMES_CLUB)))
    if account is None:
        raise RuntimeError(f"{GAMES_CLUB.name} has not signed up — the clubs run first")
    return account.club_id


async def _the_crowd(
    session: AsyncSession, her: UUID, cohort: Sequence[UUID], now: Instant
) -> tuple[UUID, ...]:
    """The cohort members who fit her and each other, in the cohort's order —
    greedily, so each one taken fits everybody taken before."""

    unfit = await build_player_fit(session).unfit_pairs(
        [her, *cohort], sport=GAMES_SPORT, kind=GAMES_KIND, at=now
    )
    taken = [her]
    for member in cohort:
        if len(taken) > CROWD:
            break
        if all(frozenset((member, other)) not in unfit for other in taken):
            taken.append(member)
    return tuple(taken[1:])


async def _the_group(
    session: AsyncSession,
    settings: Settings,
    her: UUID,
    club_id: UUID,
    crowd: Sequence[UUID],
    now: Instant,
) -> tuple[UUID, bool]:
    """Her group at the club, created once; everybody in the crowd joins it —
    joining again records nothing."""

    group_id = await _games_group_of(session, her, club_id)
    created = group_id is None
    if group_id is None:
        group_id = await CreatePlayerGroup(
            groups=group_repository(session),
            clubs=build_home_clubs(session),
            codes=build_group_code_minter(session),
            uow=build_unit_of_work(session),
            clock=FixedClock(at=now),
        ).execute(
            CreatePlayerGroupCommand(
                creator_id=her,
                name=GAMES_GROUP,
                home_club_id=club_id,
                join_policy=JoinPolicy.ANYONE,
            )
        )
    for member in crowd:
        await join_group(session, settings, group_id, member, FixedClock(at=now))
    return group_id, created


async def _games_group_of(
    session: AsyncSession, her: UUID, club_id: UUID
) -> UUID | None:
    directory = build_group_directory(session)
    listings = await directory.listings(await directory.groups_of(her))
    return next(
        (
            listing.id
            for listing in listings.values()
            if listing.owner_id == her
            and listing.home_club_id == club_id
            and listing.name == GroupName(GAMES_GROUP)
        ),
        None,
    )


async def her_games_group(session: AsyncSession) -> tuple[UUID, UUID] | None:
    """The protagonist, and the group this layer deals her games in — ``None``
    before a run has gathered it. What the screens read her deck from."""

    her = await _protagonist(session)
    group_id = await _games_group_of(session, her, await _club_id(session))
    return None if group_id is None else (her, group_id)


async def _free_at(
    session: AsyncSession,
    her: UUID,
    crowd: Sequence[UUID],
    club_id: UUID,
    now: Instant,
) -> dict[Instant, tuple[UUID, ...]]:
    """The first hour on each day from ``LEAD`` out that the club sells padel,
    **she is free for the whole of, and so are three of the crowd** — and who
    of the crowd is, in the crowd's order. *Free* is the mechanics §4.2's: the
    weekly hours cover the whole game, never merely its start."""

    offer = (
        await build_sellable_court_hours(session).between(
            [club_id], start=now + LEAD, end=now + HORIZON, now=now
        )
    ).get(club_id)
    profiles = _profiles(session)
    weeks = {
        player: profile.weekly_hours
        for player in (her, *crowd)
        if (profile := await profiles.load(player)) is not None
    }
    if offer is None or her not in weeks:
        return {}
    days: dict[date, Instant] = {}
    free: dict[Instant, tuple[UUID, ...]] = {}
    for hour in offer.hours:
        day = hour.start.astimezone(offer.zone).date()
        if hour.sport is not GAMES_SPORT or day in days:
            continue
        if not free_for_the_hour(weeks[her], start=hour.start, zone=offer.zone):
            continue
        members = tuple(
            member
            for member in crowd
            if member in weeks
            and free_for_the_hour(weeks[member], start=hour.start, zone=offer.zone)
        )
        if len(members) >= max(IN_ON_EACH):
            days[day] = hour.start
            free[hour.start] = members
    return free


async def _filling_at(
    session: AsyncSession, her: UUID, group_id: UUID, now: Instant
) -> dict[Instant, tuple[UUID, tuple[UUID, ...], int]]:
    """The picks already filling in the group, by hour: each one's id, the
    three named beside her, and how many of them are In."""

    proposals = build_proposal_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    found: dict[Instant, tuple[UUID, tuple[UUID, ...], int]] = {}
    for proposal_id in await build_proposal_directory(session).filling_in(
        group_id, now=now
    ):
        proposal = await proposals.load(proposal_id)
        if proposal is None or proposal.origin is not Origin.PICK:
            continue
        named = tuple(
            player
            for version in proposal.versions
            for player in version.players
            if player != her
        )
        said = sum(1 for player in named if player in proposal.yeses)
        found.setdefault(proposal.start, (proposal_id, named, said))
    return found


async def _says_yes(
    session: AsyncSession, clock: FixedClock, proposal_id: UUID, player: UUID
) -> None:
    await SayYes(
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ),
        guards=build_proposal_guards(session),
        uow=build_unit_of_work(session),
        clock=clock,
    ).execute(AnswerProposalCommand(proposal_id=proposal_id, player_id=player))


def _profiles(session: AsyncSession) -> PlayerProfileRepository:
    return build_player_profile_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def proposal_lines(seeded: SeededProposals) -> list[str]:
    """The report's section: the group, and each pick with who is In."""

    lines = [
        f"Games still filling — {GAMES_GROUP} at {GAMES_CLUB.name}, "
        f"{'created' if seeded.created_group else 'already there'}, "
        f"{seeded.crowd} of the cohort fit {THE_POPULATED_PLAYER.email}:"
    ]
    for pick in seeded.picks:
        state = "made" if pick.made else "already filling"
        lines.append(
            f"  {pick.start.astimezone(CLUB_ZONE):%a %d %b %H:%M} · "
            f"{pick.in_count} of 3 In · {state}"
        )
    return lines
