"""The groups: four player groups at the seeded clubs, created and joined by the
named accounts.

**A seeded group is a group somebody created and others joined**
(``docs/adr/0029``): each one goes through ``CreatePlayerGroup`` as its Owner
would, and each member through ``JoinGroup`` — so a group has a stream, its
projections are written by the repository's own ``save``, and its link carries a
code minted by the same minter a request uses. Nothing here opens a table.

**The members are the named accounts and never the cohort**, because what a
group shows is decided by who is rated in what, and the catalog is where those
facts are named: the cohort is padel and tennis throughout, and only
``rated-in-every-sport`` holds squash and badminton. So the dots come out as the
rule says they must — padel where four members play it, tennis where exactly two
do, and **no** squash or badminton dot anywhere, because one member rated in a
sport is not a dot.

**The arrangement is for the screens a developer signs in to.** The default
protagonist owns one group and joined another later, so her Groups list has two
rows, newest joined first; she is in neither group at Wisła Park, so searching
*b* shows her a *Join*; ``the-newcomer`` is in no group, which is the empty
state; and ``rated-in-every-sport`` owns a group nobody has joined, which is
*just you so far*. Every group is *Anyone*: a group that needs approval admits
nobody by a tap until join requests exist (#505).

**Written in the past**, each group created some days before the run and each
member joining an hour after the one before, so *newest joined first* and *the
first to join* have an order to show rather than a tie.

**Re-running creates nobody's group twice.** A group has no natural key — names
are not unique — so it is found as the Owner's own group of that name at that
club; joining again records nothing, by the rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_club_account_repository,
    build_domain_event_store,
    build_event_publisher,
    build_group_code_minter,
    build_group_directory,
    build_group_repository,
    build_home_clubs,
    build_rated_group_members,
    build_unit_of_work,
    build_user_repository,
)
from app.kernel import Instant
from app.modules.groups.application.commands import (
    CreatePlayerGroupCommand,
    JoinGroupCommand,
)
from app.modules.groups.application.create_player_group import CreatePlayerGroup
from app.modules.groups.application.join_group import JoinGroup
from app.modules.groups.domain.ports import GroupDirectory, GroupRepository
from app.modules.groups.domain.value_objects import GroupName, JoinPolicy
from app.modules.users.domain.ports import UserRepository
from app.modules.users.domain.value_objects import Email
from app.seeds.catalog import (
    ASSESSMENT_COMPLETED,
    BRAND_NEW_PLAYER,
    RATED_IN_EVERY_SPORT,
    RATING_BARELY_ESTABLISHED,
    RATING_WELL_ESTABLISHED,
    THE_BLANK_WEEK_PLAYER,
    THE_ONE_SPORT_PLAYER,
    THE_POPULATED_PLAYER,
    SeedAccount,
)
from app.seeds.clock import hours_before
from app.seeds.clubs import SEED_CLUBS, SeedClub, desk_email


def _club(name: str) -> SeedClub:
    return next(club for club in SEED_CLUBS if club.name == name)


@final
@dataclass(frozen=True, slots=True)
class SeedGroup:
    """One group as its Owner would create it, and who joined it after."""

    name: str
    club: SeedClub
    owner: SeedAccount
    members: tuple[SeedAccount, ...]
    #: How long before the run the Owner created it.
    days_ago: int


SEED_GROUPS: Final[tuple[SeedGroup, ...]] = (
    SeedGroup(
        "Czwartkowy padel",
        _club("Centrum Ruchu"),
        owner=THE_POPULATED_PLAYER,
        members=(
            THE_ONE_SPORT_PLAYER,
            RATING_WELL_ESTABLISHED,
            RATING_BARELY_ESTABLISHED,
        ),
        days_ago=21,
    ),
    SeedGroup(
        "Bonarka weekend",
        _club("Bonarka Arena"),
        owner=RATED_IN_EVERY_SPORT,
        members=(THE_POPULATED_PLAYER, ASSESSMENT_COMPLETED, BRAND_NEW_PLAYER),
        days_ago=14,
    ),
    SeedGroup(
        "Błonia po pracy",
        _club("Wisła Park"),
        owner=THE_BLANK_WEEK_PLAYER,
        members=(RATED_IN_EVERY_SPORT,),
        days_ago=9,
    ),
    SeedGroup(
        "Squash po pracy",
        _club("Zabłocie Sport"),
        owner=RATED_IN_EVERY_SPORT,
        members=(),
        days_ago=4,
    ),
)

# Refused on import, through the domain's own value object, as the clubs' are:
# a name the New group form would refuse fails here rather than half way
# through a run.
for _group in SEED_GROUPS:
    GroupName(_group.name)


@final
@dataclass(frozen=True, slots=True)
class SeededGroup:
    group: SeedGroup
    group_id: UUID
    #: Whether this run created it, or found it already there.
    created: bool


@final
@dataclass(frozen=True, slots=True)
class SeededGroups:
    groups: tuple[SeededGroup, ...]


async def write_the_groups(
    session_factory: async_sessionmaker[AsyncSession], *, now: Instant
) -> SeededGroups:
    """Create every declared group that its Owner has not created yet, and join
    every declared member to it.

    **After the accounts and the clubs**, which it reads and never writes: an
    Owner or a member the accounts layer did not make, or a club the clubs layer
    did not sign up, is a run in the wrong order and fails loudly.
    """

    async with session_factory() as session:
        users = build_user_repository(session)
        directory = build_group_directory(session)
        seeded: list[SeededGroup] = []
        for declared in SEED_GROUPS:
            owner_id = await _player_id(users, declared.owner)
            club_id = await _club_id(session, declared.club)
            hours_ago = declared.days_ago * 24
            group_id = await _the_owners_group(directory, owner_id, declared, club_id)
            created = group_id is None
            if group_id is None:
                group_id = await CreatePlayerGroup(
                    groups=_repository(session),
                    clubs=build_home_clubs(session),
                    codes=build_group_code_minter(session),
                    uow=build_unit_of_work(session),
                    clock=hours_before(now, hours_ago),
                ).execute(
                    CreatePlayerGroupCommand(
                        creator_id=owner_id,
                        name=declared.name,
                        home_club_id=club_id,
                        join_policy=JoinPolicy.ANYONE,
                    )
                )
            for hour, member in enumerate(declared.members, start=1):
                await JoinGroup(
                    groups=_repository(session),
                    directory=directory,
                    ratings=build_rated_group_members(session),
                    uow=build_unit_of_work(session),
                    clock=hours_before(now, hours_ago - hour),
                ).execute(
                    JoinGroupCommand(
                        group_id=group_id, player_id=await _player_id(users, member)
                    )
                )
            seeded.append(
                SeededGroup(group=declared, group_id=group_id, created=created)
            )
    return SeededGroups(groups=tuple(seeded))


def _repository(session: AsyncSession) -> GroupRepository:
    return build_group_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


async def _player_id(users: UserRepository, account: SeedAccount) -> UUID:
    user = await users.get_by_email(account.email)
    if user is None:
        raise RuntimeError(
            f"{account.slug} is not registered — the accounts layer runs first"
        )
    return user.id


async def _club_id(session: AsyncSession, club: SeedClub) -> UUID:
    """The club **its desk** signed up — found by the desk's address rather than
    by the club's name, which is not unique: a developer may sign up a second
    *Bonarka Arena* by hand."""

    accounts = build_club_account_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    account = await accounts.get_by_email(Email(desk_email(club)))
    if account is None:
        raise RuntimeError(
            f"{club.name} has not signed up — the clubs layer runs first"
        )
    return account.club_id


async def _the_owners_group(
    directory: GroupDirectory, owner_id: UUID, declared: SeedGroup, club_id: UUID
) -> UUID | None:
    """The group of this name at this club that this Owner already created."""

    listings = await directory.listings(await directory.groups_of(owner_id))
    for listing in listings.values():
        if (
            listing.owner_id == owner_id
            and listing.home_club_id == club_id
            and listing.name == GroupName(declared.name)
        ):
            return listing.id
    return None


def group_lines(seeded: SeededGroups) -> list[str]:
    """The report's section: every group, where it is, who runs it, who is in it."""

    new = sum(1 for entry in seeded.groups if entry.created)
    lines = [
        f"Groups — {len(seeded.groups)} player groups at the seeded clubs, {new} "
        f"created by this run. Every one is Anyone:"
    ]
    for entry in seeded.groups:
        group = entry.group
        state = "created" if entry.created else "already there"
        lines.append(
            f"  {group.name} · {group.club.name} · owned by {group.owner.email} · "
            f"{1 + len(group.members)} members · {state}"
        )
    return lines
