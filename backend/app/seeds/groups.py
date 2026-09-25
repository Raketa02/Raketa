"""The groups: five player groups at the seeded clubs, created and joined by the
named accounts — and one Join request left waiting.

**A seeded group is a group somebody created and others joined**
(``docs/adr/0029``): each one goes through ``CreatePlayerGroup`` as its Owner
would, and each member through ``JoinGroup`` — and, on a *People I approve*
group, through the Owner's ``ApproveJoinRequest`` after it, because a tap there
is a request and only the Owner lets anybody in. So a group has a stream, its
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
*just you so far*. **One group is *People I approve*, and it is hers**, with one
member she let in and one request waiting — from ``rated-in-every-sport``, whose
four sports are the longest request card there is (club 20's *Tomek K.*), and
whose join search shows *requested · waiting* on it (#505).

**Written in the past**, each group created some days before the run and each
member joining an hour after the one before, so *newest joined first* and *the
first to join* have an order to show rather than a tie.

**Re-running creates nobody's group twice.** A group has no natural key — names
are not unique — so it is found as the Owner's own group of that name at that
club; joining again, asking again while waiting and approving a member again
each record nothing, by the rule. A request the developer answered in the app is
put back as waiting only if it was declined — the person asks again, which is
what declining allows.
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
    build_group_faces,
    build_group_repository,
    build_home_clubs,
    build_rated_group_members,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings
from app.kernel import Clock, Instant
from app.modules.groups.application.answer_join_request import ApproveJoinRequest
from app.modules.groups.application.commands import (
    AnswerJoinRequestCommand,
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
    """One group as its Owner would create it, who joined it after, and who is
    still waiting to be let in."""

    name: str
    club: SeedClub
    owner: SeedAccount
    members: tuple[SeedAccount, ...]
    #: How long before the run the Owner created it.
    days_ago: int
    join_policy: JoinPolicy = JoinPolicy.ANYONE
    #: Whose Join request is left waiting — only on a *People I approve* group.
    waiting: tuple[SeedAccount, ...] = ()


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
    SeedGroup(
        "Ogrody wieczorem",
        _club("Ogrody 33"),
        owner=THE_POPULATED_PLAYER,
        members=(RATING_WELL_ESTABLISHED,),
        days_ago=30,
        join_policy=JoinPolicy.PEOPLE_I_APPROVE,
        waiting=(RATED_IN_EVERY_SPORT,),
    ),
)

# Refused on import, through the domain's own value object, as the clubs' are:
# a name the New group form would refuse fails here rather than half way
# through a run.
for _group in SEED_GROUPS:
    GroupName(_group.name)
    # A request can only wait on a group that turns a tap into one.
    if _group.waiting and _group.join_policy is not JoinPolicy.PEOPLE_I_APPROVE:
        raise ValueError(f"{_group.name} admits at once, so nobody can wait on it")


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
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
) -> SeededGroups:
    """Create every declared group that its Owner has not created yet, join
    every declared member to it — letting each in as its Owner, where the group
    needs approval — and leave every declared request waiting.

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
                        join_policy=declared.join_policy,
                    )
                )
            for hour, member in enumerate(declared.members, start=1):
                clock = hours_before(now, hours_ago - hour)
                member_id = await _player_id(users, member)
                await _join(session, settings, group_id, member_id, clock)
                if declared.join_policy is JoinPolicy.PEOPLE_I_APPROVE:
                    await ApproveJoinRequest(
                        groups=_repository(session),
                        uow=build_unit_of_work(session),
                        clock=clock,
                    ).execute(
                        AnswerJoinRequestCommand(
                            group_id=group_id, player_id=member_id, answered_by=owner_id
                        )
                    )
            for hour, asker in enumerate(
                declared.waiting, start=len(declared.members) + 1
            ):
                await _join(
                    session,
                    settings,
                    group_id,
                    await _player_id(users, asker),
                    hours_before(now, hours_ago - hour),
                )
            seeded.append(
                SeededGroup(group=declared, group_id=group_id, created=created)
            )
    return SeededGroups(groups=tuple(seeded))


async def _join(
    session: AsyncSession,
    settings: Settings,
    group_id: UUID,
    player_id: UUID,
    clock: Clock,
) -> None:
    """The player's tap — a membership on an *Anyone* group, a Join request on
    one that needs approval."""

    await JoinGroup(
        groups=_repository(session),
        directory=build_group_directory(session),
        ratings=build_rated_group_members(session),
        faces=build_group_faces(session, settings=settings),
        uow=build_unit_of_work(session),
        clock=clock,
    ).execute(JoinGroupCommand(group_id=group_id, player_id=player_id))


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
        f"created by this run:"
    ]
    for entry in seeded.groups:
        group = entry.group
        state = "created" if entry.created else "already there"
        policy = (
            "Anyone" if group.join_policy is JoinPolicy.ANYONE else "People I approve"
        )
        lines.append(
            f"  {group.name} · {group.club.name} · owned by {group.owner.email} · "
            f"{1 + len(group.members)} members · {policy} · {state}"
        )
        lines.extend(f"    waiting to join: {asker.email}" for asker in group.waiting)
    return lines
