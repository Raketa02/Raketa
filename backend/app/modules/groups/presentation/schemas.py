"""The player surface's shapes for groups and home-club search.

**The requests declare types and nothing else.** A name's length is the value
object's rule and is refused with ``group_name_invalid`` under
``details.field``, because the New group form writes its sentence under the
field it names; a bound restated here would refuse the same input first, as a
``422 validation_error`` naming no field. What stays here is what no person
types: a club's id and a join policy are refused before they are read.

**One row, three frames** (``application/views.py``): a group's name, monogram,
dots and member count cross in one shape wherever a group is drawn, and each
response adds only what its surface alone says.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.kernel import Sport
from app.modules.groups.application.views import (
    ClubCard,
    GroupAtClub,
    GroupPage,
    GroupRow,
    HomeClubResults,
    MyGroup,
    NamedClub,
)
from app.modules.groups.domain.link import group_link
from app.modules.groups.domain.monogram import MONOGRAM_COLOURS
from app.modules.groups.domain.ports import GroupFace
from app.modules.groups.domain.value_objects import GroupRelation, JoinPolicy

OMITTED: Any = None


class CreatePlayerGroupRequest(BaseModel):
    """A player creates a group. **No sport is asked for**: the group plays
    whatever its members are rated in (``docs/adr/0183`` §6)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description=(
            "Trimmed, runs of whitespace collapsed, then 1–40 characters. Never "
            "unique. Refused with `group_name_invalid`, `details.field` `name`."
        )
    )
    home_club_id: UUID = Field(
        description=(
            "A club from home-club search — **required**. A club Raketa does not "
            "have is `home_club_unknown`, `details.field` `home_club_id`."
        )
    )
    join_policy: JoinPolicy = Field(
        description="`ANYONE` (the form's default) or `PEOPLE_I_APPROVE`."
    )


class MonogramSchema(BaseModel):
    """The group's tile, **cut by the backend** so every client draws the same
    one (``docs/adr/0183`` §5)."""

    letters: str = Field(
        description=(
            "The first character of each of the first two words, as typed, or "
            "the first two characters of a one-word name: *my raketa group* is "
            "`mr`, *Ogrody 33 Club* is `O3`. Draw it as it comes — never change "
            "its case."
        )
    )
    colour: int = Field(
        ge=0,
        lt=MONOGRAM_COLOURS,
        description=(
            f"A colour **key** from 0 to {MONOGRAM_COLOURS - 1}, fixed for the "
            "group for ever — derived from its id, so a rename keeps it. Map it "
            "to your own palette; the backend never names a colour."
        ),
    )


class ClubNameSchema(BaseModel):
    """The group's home club, as a line under its name."""

    id: UUID
    name: str

    @classmethod
    def from_view(cls, club: NamedClub) -> "ClubNameSchema":
        return cls(id=club.id, name=club.name)


class GroupRowSchema(BaseModel):
    """A group, as every list draws it."""

    id: UUID
    name: str
    monogram: MonogramSchema
    sports: list[Sport] = Field(
        description=(
            "The sport dots, in the registry's order: each sport **at least two** "
            "members hold a Skill rating in. Read when the group is read — a "
            "rating earned or a member leaving moves them on the next read."
        )
    )
    member_count: int = Field(
        description="Every Group member, the Owner included. The same for every reader."
    )

    @staticmethod
    def fields_of(row: GroupRow) -> dict:
        return {
            "id": row.id,
            "name": row.name,
            "monogram": MonogramSchema(
                letters=row.monogram.letters, colour=row.monogram.colour
            ),
            "sports": list(row.sports),
            "member_count": row.member_count,
        }


class MyGroupSchema(GroupRowSchema):
    """A card on the reader's Groups list."""

    home_club: ClubNameSchema

    @classmethod
    def from_view(cls, group: MyGroup) -> "MyGroupSchema":
        return cls(
            **GroupRowSchema.fields_of(group.row),
            home_club=ClubNameSchema.from_view(group.home_club),
        )


class MyGroupsResponse(BaseModel):
    groups: list[MyGroupSchema] = Field(
        description=(
            "Every group the reader belongs to, **newest joined first**. Empty "
            "for a player in none."
        )
    )


class GroupAtClubSchema(GroupRowSchema):
    """A group inside a club's card, with what it is to the reader."""

    join_policy: JoinPolicy
    relation: GroupRelation = Field(
        description=(
            "`MEMBER` — the reader is in it (*you're in*); `NONE` — they are "
            "not, and *Join* is the tap."
        )
    )

    @classmethod
    def from_view(cls, group: GroupAtClub) -> "GroupAtClubSchema":
        return cls(
            **GroupRowSchema.fields_of(group.row),
            join_policy=group.join_policy,
            relation=group.relation,
        )


class HomeClubSchema(BaseModel):
    """One club a player could set as a group's home."""

    id: UUID
    name: str
    district: str
    distance_km: float | None = Field(
        description=(
            "From the reader's Location area to the club, one decimal and never "
            "below `0.1`. **`null` for a reader with no Location area**, whose "
            "clubs come A–Z."
        )
    )
    sports: list[Sport] = Field(
        description="What the club offers, in the registry's order."
    )
    groups: list[GroupAtClubSchema] = Field(
        description=(
            "**Every** group at this club, the biggest crowd first. Empty for a "
            "club with none — and a club with some is the one the form tints and "
            "tags *group already here*."
        )
    )

    @classmethod
    def from_view(cls, card: ClubCard) -> "HomeClubSchema":
        return cls(
            id=card.club.id,
            name=card.club.name,
            district=card.club.district,
            distance_km=card.distance_km,
            sports=list(card.club.sports),
            groups=[GroupAtClubSchema.from_view(group) for group in card.groups],
        )


class HomeClubPageResponse(BaseModel):
    clubs: list[HomeClubSchema] = Field(
        description=(
            "Nearest first, then by name — or A–Z for a reader with no Location area."
        )
    )
    next_page: int | None = Field(
        description="The page to ask for next, or `null` when this was the last."
    )

    @classmethod
    def from_view(cls, results: HomeClubResults) -> "HomeClubPageResponse":
        return cls(
            clubs=[HomeClubSchema.from_view(card) for card in results.clubs],
            next_page=results.next_page,
        )


class GroupPersonSchema(BaseModel):
    """A member's face — **a name and a photograph, and nothing else**."""

    player_id: UUID
    name: str | None = Field(
        description=(
            "The whole Name, never the nickname. `null` for an account that can "
            "no longer be named — the member keeps their seat."
        )
    )
    photo_id: UUID = Field(
        OMITTED,
        description=(
            "Their current photograph. Omitted when they have none, and omitted "
            "together with `photo_url` — draw their initials."
        ),
    )
    photo_url: str = Field(
        OMITTED,
        description=(
            "A short-lived signed link to that photograph, minted for **this "
            "response**."
        ),
    )

    @classmethod
    def from_view(cls, face: GroupFace) -> "GroupPersonSchema":
        fields: dict = {"player_id": face.player_id, "name": face.name}
        if face.photo_id is not None and face.photo_url is not None:
            fields["photo_id"] = face.photo_id
            fields["photo_url"] = face.photo_url
        return cls(**fields)


class GroupSportSchema(BaseModel):
    """One sport's *N of M* for the Games tab."""

    sport: Sport
    rated_count: int = Field(description="How many members hold a Skill rating in it.")
    first_rated: list[GroupPersonSchema] = Field(
        description=(
            "The first members to join who are rated in it, in joining order — "
            "**at most as many as the sport seats**, the faces that fill its "
            "seats."
        )
    )


class GroupResponse(GroupRowSchema):
    """A group, as one of its members opens it."""

    home_club: ClubNameSchema
    link: str = Field(
        description=(
            "The Group link: the public site's address, `/join/` and the group's "
            "code. **It never changes** — not on a rename, a policy change or a "
            "handover."
        )
    )
    join_policy: JoinPolicy
    is_owner: bool = Field(description="Whether the reader is the group's Owner.")
    rated_by_sport: list[GroupSportSchema] = Field(
        description=(
            "**Every sport**, in the registry's order — one the group has no dot "
            "for too, because the reader may be rated in it and open it."
        )
    )

    @classmethod
    def from_view(cls, page: GroupPage, *, public_site: str) -> "GroupResponse":
        return cls(
            **GroupRowSchema.fields_of(page.row),
            home_club=ClubNameSchema.from_view(page.home_club),
            link=group_link(public_site, page.code),
            join_policy=page.join_policy,
            is_owner=page.is_owner,
            rated_by_sport=[
                GroupSportSchema(
                    sport=sport.sport,
                    rated_count=sport.rated_count,
                    first_rated=[
                        GroupPersonSchema.from_view(face) for face in sport.first_rated
                    ],
                )
                for sport in page.by_sport
            ],
        )
