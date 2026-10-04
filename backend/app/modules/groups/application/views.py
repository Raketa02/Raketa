"""What the Groups use cases answer: a group as each surface draws it.

**One row, three frames.** A group's name, monogram, dots and member count are
the same wherever it is drawn — the Groups list, a club's card in a search, the
group's own page — so they are one ``GroupRow``, built by one function, and each
surface adds only what it alone says: the home club on the list, the policy,
the Owner's name and the reader's relation in a search, the link and each
sport's *N of M* on the page.

**One card, two searches.** Home-club search and join search both answer club
cards with groups inside (``docs/adr/0183`` §9), and both build them with
``club_cards`` — so a group drawn in either is one shape, and the answer to a
tap on it patches either in place.

**Both kinds, one row.** An official group's dots are the sports it declares,
and who answers its requests is the account running it now rather than an
Owner (``docs/adr/0183`` §3, §6) — each said once, here, so no surface draws
an official group as a player group with a null where its Owner would be.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import final
from uuid import UUID

from app.kernel import Sport
from app.modules.groups.domain.home_club_search import ClubPage, in_card_order
from app.modules.groups.domain.join_search import ReadAs
from app.modules.groups.domain.monogram import Monogram, monogram_of
from app.modules.groups.domain.ports import (
    GroupAdministrators,
    GroupFace,
    GroupFaces,
    GroupListing,
    HomeClub,
    RatedGroupMembers,
    RunningAdministrator,
    SportLevel,
)
from app.modules.groups.domain.sports import sport_dots
from app.modules.groups.domain.value_objects import (
    GroupCode,
    GroupKind,
    GroupRelation,
    JoinPolicy,
)


@final
@dataclass(frozen=True, slots=True)
class GroupRow:
    id: UUID
    kind: GroupKind
    name: str
    monogram: Monogram
    #: The sport dots, in the registry's order — what a player group's members
    #: play, and what an official group declares.
    sports: tuple[Sport, ...]
    member_count: int


@final
@dataclass(frozen=True, slots=True)
class NamedClub:
    id: UUID
    name: str


@final
@dataclass(frozen=True, slots=True)
class MyGroup:
    """A row on the reader's own Groups list."""

    row: GroupRow
    home_club: NamedClub


@final
@dataclass(frozen=True, slots=True)
class GroupAtClub:
    """A group inside a club's card, as a reader who may join it sees it.

    ``owner_name`` is the Owner's **Name** — who answers a Join request, for the
    *approves joins* line — or ``None`` for an account ``users`` can no longer
    name, and on an official group, which has no Owner. ``administrator_name``
    is an official group's counterpart: the Name of the account running it,
    ``None`` while nobody does. ``is_administrator``
    is whether **the reader** runs it — and joins it directly, whatever its
    policy (``docs/adr/0183`` §7).
    """

    row: GroupRow
    join_policy: JoinPolicy
    owner_name: str | None
    relation: GroupRelation
    administrator_name: str | None
    is_administrator: bool


@final
@dataclass(frozen=True, slots=True)
class ClubCard:
    club: HomeClub
    distance_km: float | None
    groups: tuple[GroupAtClub, ...]


@final
@dataclass(frozen=True, slots=True)
class HomeClubResults:
    clubs: tuple[ClubCard, ...]
    next_page: int | None


@final
@dataclass(frozen=True, slots=True)
class JoinSearchResults:
    """What join search found, and **what it read the text as** — so an empty
    answer to a link is *nothing at that link* and an empty answer to text is
    *no match*, two different sentences (#500 stories 37 and 38)."""

    clubs: tuple[ClubCard, ...]
    next_page: int | None
    read_as: ReadAs


@final
@dataclass(frozen=True, slots=True)
class RequestCard:
    """A Join request as its Owner sees it — club 20's card: who is asking, a
    name and a face, and every sport they are rated in with its Level."""

    face: GroupFace
    levels: tuple[SportLevel, ...]


@final
@dataclass(frozen=True, slots=True)
class MemberRow:
    """One row of Members, for one sport — play 61's: who, their Level in it
    and their Player Score (*Padel 2,71 · score 92*), whether they own the group,
    and when they joined.

    ``player_score`` is ``None`` for somebody the platform has watched nothing
    of, which the row prints as no score rather than a nought.
    ``is_administrator`` is the account running an official group, who joined
    it as a player — the row the **admin** tag is drawn on, as it is on a player
    group's Owner's."""

    face: GroupFace
    level: float
    player_score: int | None
    is_owner: bool
    joined_at: datetime
    is_administrator: bool


@final
@dataclass(frozen=True, slots=True)
class SportFaces:
    """One sport's *N of M*: how many members are rated in it, and the faces of
    the first of them to join, as many as the sport seats."""

    sport: Sport
    rated_count: int
    first_rated: tuple[GroupFace, ...]


@final
@dataclass(frozen=True, slots=True)
class GroupPage:
    """A group as one of its members opens it."""

    row: GroupRow
    home_club: NamedClub
    code: GroupCode
    join_policy: JoinPolicy
    is_owner: bool
    by_sport: tuple[SportFaces, ...]
    #: The Info tab's members row: everybody the reader may see but the
    #: reader, in the Members list's order, at most five (``domain/members.py``).
    member_faces: tuple[GroupFace, ...]
    #: An official group's *approves joins* line, as a club's card says it
    #: (``approver_name``) — ``None`` while nobody runs it, and on a player
    #: group. ``is_administrator`` is whether the reader runs it (#510).
    administrator_name: str | None
    is_administrator: bool


@final
@dataclass(frozen=True, slots=True)
class LinkedGroup:
    """A group as a stranger holding its link sees it, on the public site
    (``docs/adr/0187`` §4–§5): the row every list draws, and where it plays —
    **and nobody in it**. There is no field here a member could be named by, so
    no surface can print one."""

    row: GroupRow
    club_name: str
    club_district: str


@final
@dataclass(frozen=True, slots=True)
class EditedGroup:
    """The group as *Edit group* left it, and who the save let in — everybody
    the switch to *Anyone* admitted, in the order they asked; nobody for every
    other save."""

    page: GroupPage
    admitted: tuple[GroupFace, ...]


def face_of(faces: Mapping[UUID, GroupFace], player_id: UUID) -> GroupFace:
    """A person's face from a ``GroupFaces`` answer — or a face with nothing on
    it for an account ``users`` could not answer for, **who keeps their place**
    (the client draws initials), because they are still in the group."""

    return faces.get(player_id, GroupFace(player_id=player_id))


def row_of(listing: GroupListing, rated: Mapping[Sport, frozenset[UUID]]) -> GroupRow:
    """The one function every surface's row comes out of."""

    return GroupRow(
        id=listing.id,
        kind=listing.kind,
        name=listing.name.value,
        monogram=monogram_of(listing.id, listing.name),
        sports=dots_of(listing, rated),
        member_count=listing.member_count,
    )


def dots_of(
    listing: GroupListing, rated: Mapping[Sport, frozenset[UUID]]
) -> tuple[Sport, ...]:
    """The one place the two kinds' dots part (``docs/adr/0183`` §6): **an
    official group's are the sports it declares**, and a player group's the
    sports two of its members are rated in."""

    if listing.kind is GroupKind.OFFICIAL:
        declared = listing.declared_sports
        if declared is None:
            raise RuntimeError(f"official group {listing.id} declares no sports")
        return declared.in_registry_order()
    return sport_dots(listing.members, rated)


async def running_administrators(
    administrators: GroupAdministrators, listings: Sequence[GroupListing]
) -> Mapping[UUID, RunningAdministrator]:
    """Who runs each of these groups now, by group id — **one question about
    the set**, asked only about the official ones, and never at all for a list
    with none. A group nobody runs is absent."""

    running = {
        listing.id: listing.administrator_id
        for listing in listings
        if listing.kind is GroupKind.OFFICIAL and listing.administrator_id is not None
    }
    if not running:
        return {}
    active = await administrators.running(set(running.values()))
    return {
        group_id: active[administrator_id]
        for group_id, administrator_id in running.items()
        if administrator_id in active
    }


async def runner_of(
    administrators: GroupAdministrators, administrator_id: UUID
) -> RunningAdministrator | None:
    """This Administrator while their administratorship is active, or
    ``None`` once it is not."""

    return (await administrators.running([administrator_id])).get(administrator_id)


async def account_running(
    administrators: GroupAdministrators, administrator_id: UUID
) -> UUID | None:
    """The account behind this Administrator while their administratorship is
    active, or ``None`` once it is not."""

    runner = await runner_of(administrators, administrator_id)
    return None if runner is None else runner.account_id


async def running_it(
    administrators: GroupAdministrators, listing: GroupListing
) -> RunningAdministrator | None:
    """Who runs this one group now — ``None`` for a player group, which no
    Administrator runs, and for an official group nobody runs."""

    if listing.kind is not GroupKind.OFFICIAL or listing.administrator_id is None:
        return None
    return await runner_of(administrators, listing.administrator_id)


async def running_account(
    administrators: GroupAdministrators, listing: GroupListing
) -> UUID | None:
    """The account running this one group now — ``None`` for a player group,
    which no Administrator runs, and for an official group nobody runs."""

    runner = await running_it(administrators, listing)
    return None if runner is None else runner.account_id


def who_runs_it(listing: GroupListing, runner: UUID | None) -> UUID | None:
    """Who comes after the reader on the Members list, and carries the
    **admin** tag (#500 story 81): a player group's Owner, and the account
    running an official group now (``runner``) — which the list reads only
    once it has joined as a player."""

    if listing.kind is GroupKind.OFFICIAL:
        return runner
    return listing.owner_id


async def rated_among(
    ratings: RatedGroupMembers, listings: Sequence[GroupListing]
) -> Mapping[Sport, frozenset[UUID]]:
    """Who is rated in what among every member of these groups — **one question
    about the union**, never one per group."""

    return await ratings.rated_in(
        {member for listing in listings for member in listing.members}
    )


def at_club(
    listing: GroupListing,
    rated: Mapping[Sport, frozenset[UUID]],
    reader_id: UUID,
    *,
    names: Mapping[UUID, str],
    runner: RunningAdministrator | None,
) -> GroupAtClub:
    """A group as a club's card draws it for this reader — the search's row and
    the join's answer, which must be one shape for the card to be patched in
    place. ``names`` holds every Name ``users`` could answer for; ``runner`` is
    who runs an official group now.

    **An official group's approver is named as a player group's Owner is** —
    by the account's Name, so the line and the admin-tagged Members row say
    one name — and by the name the club gave them only where ``users`` has
    none to answer with: an account an invitation opened, whose Name is that
    name (``docs/adr/0185`` §4).
    """

    owner_name = (
        names.get(listing.owner_id)
        if listing.kind is GroupKind.PLAYER and listing.owner_id is not None
        else None
    )
    return GroupAtClub(
        row=row_of(listing, rated),
        join_policy=listing.join_policy,
        owner_name=owner_name,
        relation=relation_of(listing, reader_id),
        administrator_name=approver_name(runner, names),
        is_administrator=runner is not None and runner.account_id == reader_id,
    )


def approver_name(
    runner: RunningAdministrator | None, names: Mapping[UUID, str]
) -> str | None:
    """Who an official group's *approves joins* line names: the account
    running it by **its** Name — the one its admin-tagged Members row says —
    and by the name the club gave them only where ``users`` has none to answer
    with (``docs/adr/0185`` §4). ``None`` while nobody runs it: the line then
    names the club (``docs/adr/0183`` §3)."""

    return None if runner is None else names.get(runner.account_id, runner.name)


def relation_of(listing: GroupListing, reader_id: UUID) -> GroupRelation:
    """In it, waiting to be let in, or neither — and a declined request is
    neither, because the request is gone (``docs/adr/0183`` §7)."""

    if reader_id in listing.members:
        return GroupRelation.MEMBER
    if reader_id in listing.waiting:
        return GroupRelation.REQUESTED
    return GroupRelation.NONE


async def at_clubs(
    listings: Sequence[GroupListing],
    *,
    reader_id: UUID,
    ratings: RatedGroupMembers,
    faces: GroupFaces,
    administrators: GroupAdministrators,
) -> dict[UUID, GroupAtClub]:
    """Each of these groups as a club's card draws it, by id — **three reads
    whatever the number of groups**: the ratings behind every dot, who runs the
    official ones, and every Owner's and runner's Name in one question."""

    rated = await rated_among(ratings, listings)
    runners = await running_administrators(administrators, listings)
    names = await faces.names_of(
        {
            listing.owner_id
            for listing in listings
            if listing.kind is GroupKind.PLAYER and listing.owner_id is not None
        }
        | {runner.account_id for runner in runners.values()}
    )
    return {
        listing.id: at_club(
            listing,
            rated,
            reader_id,
            names=names,
            runner=runners.get(listing.id),
        )
        for listing in listings
    }


async def club_cards(
    page: ClubPage,
    groups_at: Mapping[UUID, Sequence[GroupListing]],
    *,
    reader_id: UUID,
    ratings: RatedGroupMembers,
    faces: GroupFaces,
    administrators: GroupAdministrators,
) -> tuple[ClubCard, ...]:
    """A page of clubs as cards, each carrying the groups ``groups_at`` gives it
    **the biggest crowd first** — every group at the club, or only the ones a
    search matched; which is the caller's to have chosen. A club absent from
    ``groups_at`` is a card with no groups: *no groups here yet*."""

    rows = await at_clubs(
        [listing for listings in groups_at.values() for listing in listings],
        reader_id=reader_id,
        ratings=ratings,
        faces=faces,
        administrators=administrators,
    )
    return tuple(
        ClubCard(
            club=placed.club,
            distance_km=placed.distance_km,
            groups=tuple(
                rows[listing.id]
                for listing in in_card_order(groups_at.get(placed.club.id, ()))
            ),
        )
        for placed in page.clubs
    )
