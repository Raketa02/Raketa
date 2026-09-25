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
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Sport
from app.modules.groups.domain.home_club_search import ClubPage, in_card_order
from app.modules.groups.domain.join_search import ReadAs
from app.modules.groups.domain.monogram import Monogram, monogram_of
from app.modules.groups.domain.ports import (
    GroupFace,
    GroupFaces,
    GroupListing,
    HomeClub,
    RatedGroupMembers,
    SportLevel,
)
from app.modules.groups.domain.sports import sport_dots
from app.modules.groups.domain.value_objects import (
    GroupCode,
    GroupRelation,
    JoinPolicy,
)


@final
@dataclass(frozen=True, slots=True)
class GroupRow:
    id: UUID
    name: str
    monogram: Monogram
    #: The sport dots, in the registry's order.
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
    name.
    """

    row: GroupRow
    join_policy: JoinPolicy
    owner_name: str | None
    relation: GroupRelation


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


def row_of(listing: GroupListing, rated: Mapping[Sport, frozenset[UUID]]) -> GroupRow:
    """The one function every surface's row comes out of."""

    return GroupRow(
        id=listing.id,
        name=listing.name.value,
        monogram=monogram_of(listing.id, listing.name),
        sports=sport_dots(listing.members, rated),
        member_count=listing.member_count,
    )


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
    owner_name: str | None,
) -> GroupAtClub:
    """A group as a club's card draws it for this reader — the search's row and
    the join's answer, which must be one shape for the card to be patched in
    place."""

    return GroupAtClub(
        row=row_of(listing, rated),
        join_policy=listing.join_policy,
        owner_name=owner_name,
        relation=relation_of(listing, reader_id),
    )


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
) -> dict[UUID, GroupAtClub]:
    """Each of these groups as a club's card draws it, by id — **two reads
    whatever the number of groups**: the ratings behind every dot, and every
    Owner's name."""

    rated = await rated_among(ratings, listings)
    names = await faces.names_of({listing.owner_id for listing in listings})
    return {
        listing.id: at_club(
            listing, rated, reader_id, owner_name=names.get(listing.owner_id)
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
