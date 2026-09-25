"""The player surface's shapes for groups, the two searches and Join requests.

**The requests declare types and nothing else.** A name's length is the value
object's rule and is refused with ``group_name_invalid`` under
``details.field``, because the New group form writes its sentence under the
field it names; a bound restated here would refuse the same input first, as a
``422 validation_error`` naming no field. What stays here is what no person
types: a club's id and a join policy are refused before they are read.

**One row, three frames** (``application/views.py``): a group's name, monogram,
dots and member count cross in one shape wherever a group is drawn, and each
response adds only what its surface alone says. **One card, two searches**:
home-club search and join search both answer ``ClubCardSchema``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.kernel import Sport
from app.modules.groups.application.views import (
    ClubCard,
    EditedGroup,
    GroupAtClub,
    GroupPage,
    GroupRow,
    HomeClubResults,
    JoinSearchResults,
    MemberRow,
    MyGroup,
    NamedClub,
    RequestCard,
)
from app.modules.groups.domain.join_search import ReadAs
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


class EditGroupRequest(BaseModel):
    """The Owner saves *Edit group* — the New group form's Name and Who can join
    cards, **both as the form holds them**. The home club is not here: it never
    changes (``docs/adr/0183`` §2)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description=(
            "Trimmed, runs of whitespace collapsed, then 1–40 characters. Refused "
            "with `group_name_invalid`, `details.field` `name`."
        )
    )
    join_policy: JoinPolicy = Field(
        description=(
            "`ANYONE` or `PEOPLE_I_APPROVE`. **Switching to `ANYONE` admits "
            "everybody waiting at once.**"
        )
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

    join_policy: JoinPolicy = Field(
        description=(
            "`ANYONE` — *Join* admits at once (*anyone can join*); "
            "`PEOPLE_I_APPROVE` — *Ask to join* leaves a request for the Owner "
            "(*Karol approves joins*)."
        )
    )
    owner_name: str | None = Field(
        description=(
            "The Owner's **whole Name**, never the nickname — who answers a "
            "request, for the *approves joins* line. **No first name is cut "
            "from it, here or by a client**: a sentence naming somebody uses the "
            "whole Name (`docs/adr/0171` §4), so the line reads *Karol Nowak "
            "approves joins* and the row truncates it as it truncates any line. "
            "`null` for an account that can no longer be named."
        )
    )
    relation: GroupRelation = Field(
        description=(
            "`MEMBER` — the reader is in it (*you're in*); `REQUESTED` — they "
            "asked and their request is waiting (*requested · waiting*); `NONE` "
            "— neither, and *Join* or *Ask to join* is the tap. **A declined "
            "request reads `NONE`**: nothing tells them it was declined, and "
            "they may ask again."
        )
    )

    @classmethod
    def from_view(cls, group: GroupAtClub) -> "GroupAtClubSchema":
        return cls(
            **GroupRowSchema.fields_of(group.row),
            join_policy=group.join_policy,
            owner_name=group.owner_name,
            relation=group.relation,
        )


class ClubCardSchema(BaseModel):
    """One club as a search draws it: its header — which is context, not a
    choice — and the groups inside it."""

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
            "The biggest crowd first. **Home-club search**: every group at the "
            "club — and a club with some is the one the New group form tints "
            "and tags *group already here*. **Join search**: every group when "
            "the club itself matched, only the groups whose name matched when "
            "it did not, and exactly the linked group for a link. Empty for a "
            "club with none: *no groups here yet*."
        )
    )

    @classmethod
    def from_view(cls, card: ClubCard) -> "ClubCardSchema":
        return cls(
            id=card.club.id,
            name=card.club.name,
            district=card.club.district,
            distance_km=card.distance_km,
            sports=list(card.club.sports),
            groups=[GroupAtClubSchema.from_view(group) for group in card.groups],
        )


class HomeClubPageResponse(BaseModel):
    clubs: list[ClubCardSchema] = Field(
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
            clubs=[ClubCardSchema.from_view(card) for card in results.clubs],
            next_page=results.next_page,
        )


class JoinSearchResponse(BaseModel):
    clubs: list[ClubCardSchema] = Field(
        description=(
            "Nearest first, then by name — or A–Z for a reader with no Location "
            "area. Empty when nothing matched."
        )
    )
    next_page: int | None = Field(
        description="The page to ask for next, or `null` when this was the last."
    )
    read_as: ReadAs = Field(
        description=(
            "What the text was read as. `LINK` — it held `/join/` and a code, "
            "and the answer is exactly that group; **`LINK` with no clubs is "
            "*nothing at that link***, a link that leads nowhere. `TEXT` — "
            "matched against clubs, districts and group names; `TEXT` with no "
            "clubs is *no match*."
        )
    )

    @classmethod
    def from_view(cls, results: JoinSearchResults) -> "JoinSearchResponse":
        return cls(
            clubs=[ClubCardSchema.from_view(card) for card in results.clubs],
            next_page=results.next_page,
            read_as=results.read_as,
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
        return cls(**GroupPersonSchema.fields_of(face))

    @staticmethod
    def fields_of(face: GroupFace) -> dict:
        """A face's fields, the photograph's two only where there is one — so a
        shape that extends this one omits them as this one does."""

        fields: dict = {"player_id": face.player_id, "name": face.name}
        if face.photo_id is not None and face.photo_url is not None:
            fields["photo_id"] = face.photo_id
            fields["photo_url"] = face.photo_url
        return fields


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
    member_faces: list[GroupPersonSchema] = Field(
        description=(
            "The Info tab's members row: **up to five** faces of everybody but "
            "the reader, in the Members list's order — the Owner, then newest "
            "joined first — with a blocked pair, either way round, left out, as "
            "the list it opens leaves them out. Empty for a reader alone "
            "(`member_count` 1), whose row draws their own face — and empty "
            "too, with `member_count` above 1, when a block hides everybody "
            "else. `member_count` is the group's, so its *+N* counts everybody."
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
            member_faces=[
                GroupPersonSchema.from_view(face) for face in page.member_faces
            ],
        )


class EditedGroupResponse(BaseModel):
    """The group as *Edit group* left it, and who the save let in."""

    group: GroupResponse = Field(
        description="The group as its page reads it, after the save."
    )
    admitted: list[GroupPersonSchema] = Field(
        description=(
            "Everybody the switch to `ANYONE` admitted, **in the order they "
            "asked** — the Edit screen shows them. Empty for every other save."
        )
    )

    @classmethod
    def from_view(
        cls, edited: EditedGroup, *, public_site: str
    ) -> "EditedGroupResponse":
        return cls(
            group=GroupResponse.from_view(edited.page, public_site=public_site),
            admitted=[GroupPersonSchema.from_view(face) for face in edited.admitted],
        )


class SportLevelSchema(BaseModel):
    """One sport somebody is rated in, and their Level in it."""

    sport: Sport
    level: float = Field(description="Their Level in it, as RacketSkill published it.")


class JoinRequestSchema(GroupPersonSchema):
    """A Join request as the Owner sees it: who is asking — ``player_id`` is the
    id to approve or decline — and what they play. **No Player Score**: the
    request card is club 20's everywhere."""

    levels: list[SportLevelSchema] = Field(
        description=(
            "**Every sport they are rated in**, in the registry's order, each "
            "with its Level — *Padel 2,44 · Tennis 2,60*. Empty for somebody "
            "rated in nothing."
        )
    )

    @classmethod
    def from_card(cls, card: RequestCard) -> "JoinRequestSchema":
        return cls(
            **GroupPersonSchema.fields_of(card.face),
            levels=[
                SportLevelSchema(sport=row.sport, level=row.level)
                for row in card.levels
            ],
        )


class JoinRequestsResponse(BaseModel):
    requests: list[JoinRequestSchema] = Field(
        description=(
            "Everybody waiting to be let in, **in the order they asked** — "
            "*Want to join · N*. Empty when nobody is waiting."
        )
    )


class GroupMemberSchema(GroupPersonSchema):
    """One row of Members, for one sport — *Padel 2,71 · score 92*."""

    level: float = Field(
        description=(
            "Their Level in the sport asked for, as RacketSkill published it. "
            "Always present: somebody not rated in it is not listed."
        )
    )
    player_score: int = Field(
        OMITTED,
        description=(
            "Their published Player Score, 0–100 — the figure their record and "
            "a player card print. **Omitted for somebody the platform has "
            "watched nothing of**, never `0`: no record is not a bad one."
        ),
    )
    is_owner: bool = Field(
        description=(
            "Whether they own the group — the row the **admin** tag is drawn on."
        )
    )
    joined_at: datetime = Field(
        description=(
            "When they joined — this stay: somebody who left and came back "
            "counts from their return."
        )
    )

    @classmethod
    def from_row(cls, row: MemberRow) -> "GroupMemberSchema":
        fields: dict = {
            **GroupPersonSchema.fields_of(row.face),
            "level": row.level,
            "is_owner": row.is_owner,
            "joined_at": row.joined_at,
        }
        if row.player_score is not None:
            fields["player_score"] = row.player_score
        return cls(**fields)


class GroupMembersResponse(BaseModel):
    sport: Sport = Field(description="The sport the list was asked for.")
    members: list[GroupMemberSchema] = Field(
        description=(
            "**Only the members rated in `sport`**: the reader first, then the "
            "Owner, then everybody else **newest joined first**. **A blocked "
            "pair, either way round, is left out of each other's list** — and "
            "nothing says so: the group's `member_count` is the same for every "
            "reader, so it may be more than the rows here. Empty when nobody in "
            "the group the reader may see is rated in it."
        )
    )
