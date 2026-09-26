"""The official groups: Ogrody 33's two WhatsApp groups, run from the app by the
administrators the club named — with players in them and one request waiting
(#509, ``docs/adr/0183`` §3).

**A seeded official group is one an Administrator created and players joined**
(``docs/adr/0029``): each goes through ``CreateOfficialGroup`` as its
administrator would, taken as the administratorship the guard would read as
active; each player through ``JoinGroup``; and, on a *People I approve* group,
through the administrator's ``ApproveJoinRequestAsAdministrator`` after it. So a
group has a stream, its projections are written by the repository's own
``save``, and its link carries a code minted by the minter a request uses.
Nothing here opens a table.

**The two are arranged for the screens the administrator tickets draw.**

- *Ogrody 33 Club* — Marta Wójcik's, the administrator-only account: *People I
  approve*, a 48-person padel WhatsApp group, three players she let in — the
  default protagonist among them, so a player signing in finds an official
  group on her list — and ``assessment-completed``'s request waiting, which is
  *Want to join · 1*.
- *Ogrody open play* — run by ``rated-in-every-sport``, the administrator who
  also plays, **and a player member of it**: *Anyone*, padel and tennis, thirty
  in the WhatsApp group. His own tap joined him directly, so his Members row
  carries the **admin** tag.

**After the administrators**, whose administratorships it reads — and runs
nothing for one the developer has removed since: a group nobody may create is
reported as skipped rather than forced.

**Re-running creates nobody's group twice.** A group is found as the one of
that name its administratorship already runs; joining again, asking again while
waiting and approving a member again each record nothing, by the rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_administrator_directory,
    build_club_account_repository,
    build_domain_event_store,
    build_event_publisher,
    build_group_administrators,
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
from app.kernel import Clock, Instant, Sport
from app.modules.groups.application.commands import (
    Administering,
    AnswerAsAdministratorCommand,
    CreateOfficialGroupCommand,
    JoinGroupCommand,
)
from app.modules.groups.application.join_group import JoinGroup
from app.modules.groups.application.official_groups import (
    ApproveJoinRequestAsAdministrator,
    CreateOfficialGroup,
)
from app.modules.groups.domain.ports import GroupRepository
from app.modules.groups.domain.value_objects import (
    DeclaredSports,
    GroupName,
    JoinPolicy,
    WhatsAppSize,
)
from app.modules.users.domain.ports import UserRepository
from app.modules.users.domain.value_objects import Email
from app.seeds.administrators import (
    ADMINISTRATOR_ONLY_EMAIL,
    PLAYER_AND_ADMINISTRATOR,
    THE_CLUB,
)
from app.seeds.catalog import (
    ASSESSMENT_COMPLETED,
    RATING_BARELY_ESTABLISHED,
    RATING_WELL_ESTABLISHED,
    THE_BLANK_WEEK_PLAYER,
    THE_ONE_SPORT_PLAYER,
    THE_POPULATED_PLAYER,
    SeedAccount,
)
from app.seeds.clock import hours_before
from app.seeds.clubs import desk_email


@final
@dataclass(frozen=True, slots=True)
class SeedOfficialGroup:
    """One official group as its administrator would create it, who joined it
    after, and who is still waiting to be let in."""

    name: str
    #: The email the administrator signs in with.
    administrator: str
    join_policy: JoinPolicy
    whatsapp_size: int
    sports: tuple[Sport, ...]
    members: tuple[SeedAccount, ...]
    #: How long before the run it was created.
    days_ago: int
    #: Whose Join request is left waiting — only on a *People I approve* group.
    waiting: tuple[SeedAccount, ...] = ()


SEED_OFFICIAL_GROUPS: Final[tuple[SeedOfficialGroup, ...]] = (
    SeedOfficialGroup(
        "Ogrody 33 Club",
        administrator=ADMINISTRATOR_ONLY_EMAIL,
        join_policy=JoinPolicy.PEOPLE_I_APPROVE,
        whatsapp_size=48,
        sports=(Sport.PADEL,),
        members=(THE_POPULATED_PLAYER, RATING_WELL_ESTABLISHED, THE_ONE_SPORT_PLAYER),
        days_ago=12,
        waiting=(ASSESSMENT_COMPLETED,),
    ),
    SeedOfficialGroup(
        "Ogrody open play",
        administrator=PLAYER_AND_ADMINISTRATOR.email,
        join_policy=JoinPolicy.ANYONE,
        whatsapp_size=30,
        sports=(Sport.PADEL, Sport.TENNIS),
        # He joined his own group as a player, first.
        members=(
            PLAYER_AND_ADMINISTRATOR,
            RATING_BARELY_ESTABLISHED,
            THE_BLANK_WEEK_PLAYER,
        ),
        days_ago=6,
    ),
)

# Refused on import, through the domain's own value objects: a group the New
# official group form would refuse fails here rather than half way through a run.
for _group in SEED_OFFICIAL_GROUPS:
    GroupName(_group.name)
    WhatsAppSize(_group.whatsapp_size)
    DeclaredSports.at_club(_group.sports, offered=THE_CLUB.sports)
    if _group.waiting and _group.join_policy is not JoinPolicy.PEOPLE_I_APPROVE:
        raise ValueError(f"{_group.name} admits at once, so nobody can wait on it")


@final
@dataclass(frozen=True, slots=True)
class SeededOfficialGroup:
    group: SeedOfficialGroup
    #: ``None`` when nothing could be created: the administratorship is not
    #: active, because the developer removed it in a walk.
    group_id: UUID | None
    #: ``created``, ``already there`` or ``skipped``.
    action: str


@final
@dataclass(frozen=True, slots=True)
class SeededOfficialGroups:
    groups: tuple[SeededOfficialGroup, ...]


async def write_the_official_groups(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
) -> SeededOfficialGroups:
    """Create every declared official group its administrator has not created
    yet, join every declared player to it — letting each in as its
    administrator, where the group needs approval — and leave every declared
    request waiting."""

    async with session_factory() as session:
        users = build_user_repository(session)
        club_id = await _club_id(session)
        seeded: list[SeededOfficialGroup] = []
        for declared in SEED_OFFICIAL_GROUPS:
            administering = await _administering(session, users, declared, club_id)
            if administering is None:
                seeded.append(SeededOfficialGroup(declared, None, "skipped"))
                continue
            hours_ago = declared.days_ago * 24
            group_id = await _the_group(session, administering, declared)
            action = "already there"
            if group_id is None:
                group_id = await CreateOfficialGroup(
                    groups=_repository(session),
                    clubs=build_home_clubs(session),
                    codes=build_group_code_minter(session),
                    uow=build_unit_of_work(session),
                    clock=hours_before(now, hours_ago),
                ).execute(
                    CreateOfficialGroupCommand(
                        administering=administering,
                        name=declared.name,
                        join_policy=declared.join_policy,
                        whatsapp_size=declared.whatsapp_size,
                        sports=declared.sports,
                    )
                )
                action = "created"
            for hour, member in enumerate(declared.members, start=1):
                clock = hours_before(now, hours_ago - hour)
                member_id = await _player_id(users, member)
                await _join(session, settings, group_id, member_id, clock)
                if declared.join_policy is JoinPolicy.PEOPLE_I_APPROVE:
                    await ApproveJoinRequestAsAdministrator(
                        groups=_repository(session),
                        uow=build_unit_of_work(session),
                        clock=clock,
                    ).execute(
                        AnswerAsAdministratorCommand(
                            administering=administering,
                            group_id=group_id,
                            player_id=member_id,
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
            seeded.append(SeededOfficialGroup(declared, group_id, action))
    return SeededOfficialGroups(groups=tuple(seeded))


async def _administering(
    session: AsyncSession,
    users: UserRepository,
    declared: SeedOfficialGroup,
    club_id: UUID,
) -> Administering | None:
    """The administratorship at the club the guard would read as active for
    this administrator's account — or ``None`` once it is not."""

    user = await users.get_by_email(declared.administrator)
    if user is None:
        raise RuntimeError(
            f"{declared.administrator} has no account — the administrators layer "
            "runs first"
        )
    for listing in await build_administrator_directory(session).active_for(user.id):
        if listing.club_id == club_id and listing.account_id is not None:
            return Administering(
                club_id=club_id,
                administrator_id=listing.id,
                account_id=listing.account_id,
            )
    return None


async def _club_id(session: AsyncSession) -> UUID:
    """The club its desk signed up — found by the desk's address rather than by
    the club's name, which is not unique."""

    accounts = build_club_account_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    account = await accounts.get_by_email(Email(desk_email(THE_CLUB)))
    if account is None:
        raise RuntimeError(
            f"{THE_CLUB.name} has not signed up — the clubs layer runs first"
        )
    return account.club_id


async def _the_group(
    session: AsyncSession, administering: Administering, declared: SeedOfficialGroup
) -> UUID | None:
    """The group of this name this administratorship already runs."""

    for listing in await build_group_directory(session).run_by(
        administering.administrator_id
    ):
        if listing.name == GroupName(declared.name):
            return listing.id
    return None


async def _join(
    session: AsyncSession,
    settings: Settings,
    group_id: UUID,
    player_id: UUID,
    clock: Clock,
) -> None:
    """The player's tap — a membership on an *Anyone* group or for the account
    that runs it, a Join request on one that needs approval."""

    await JoinGroup(
        groups=_repository(session),
        directory=build_group_directory(session),
        ratings=build_rated_group_members(session),
        faces=build_group_faces(session, settings=settings),
        administrators=build_group_administrators(session),
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


def official_group_lines(seeded: SeededOfficialGroups) -> list[str]:
    """The report's section: each official group, who runs it, who is in it."""

    lines = [
        f"Official groups — {len(seeded.groups)} at {THE_CLUB.name}, run from the "
        "app by its administrators:"
    ]
    for entry in seeded.groups:
        group = entry.group
        policy = (
            "Anyone" if group.join_policy is JoinPolicy.ANYONE else "People I approve"
        )
        sports = ", ".join(sport.value.lower() for sport in group.sports)
        lines.append(
            f"  {group.name} · run by {group.administrator} · {policy} · "
            f"WhatsApp {group.whatsapp_size} · {sports} · "
            f"{len(group.members)} players · {entry.action}"
        )
        lines.extend(f"    waiting to join: {asker.email}" for asker in group.waiting)
    return lines
