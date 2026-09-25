"""What the Groups use cases answer: a group as each surface draws it.

**One row, three frames.** A group's name, monogram, dots and member count are
the same wherever it is drawn — the Groups list, a club's card in a search, the
group's own page — so they are one ``GroupRow``, built by one function, and each
surface adds only what it alone says: the home club on the list, the policy and
the reader's relation in a search, the link and each sport's *N of M* on the
page.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Sport
from app.modules.groups.domain.monogram import Monogram, monogram_of
from app.modules.groups.domain.ports import (
    GroupFace,
    GroupListing,
    HomeClub,
    RatedGroupMembers,
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
    """A group inside a club's card, as a reader who may join it sees it."""

    row: GroupRow
    join_policy: JoinPolicy
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
    listing: GroupListing, rated: Mapping[Sport, frozenset[UUID]], reader_id: UUID
) -> GroupAtClub:
    """A group as a club's card draws it for this reader — the search's row and
    the join's answer, which must be one shape for the card to be patched in
    place."""

    return GroupAtClub(
        row=row_of(listing, rated),
        join_policy=listing.join_policy,
        relation=(
            GroupRelation.MEMBER if reader_id in listing.members else GroupRelation.NONE
        ),
    )
