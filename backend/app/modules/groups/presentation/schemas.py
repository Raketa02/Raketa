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

**Every row says its kind** (``docs/adr/0183`` §1), so a client never reads an
official group as a player group with a null where its Owner would be. The
administrator's shapes — the Groups tab, an official group's page and its
settings — come after the player's, on the administrator surface's paths; the
club's — its Groups table and the handover — on the club surface's (#510); and
last, the public site's one shape, which **carries nobody in the group**
(``docs/adr/0187`` §5).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.engines.matchfit.core import ReliabilityBand
from app.kernel import Sport
from app.modules.groups.application.club_groups import (
    ClubGroupRow,
    ClubGroupAdministrator,
)
from app.modules.groups.application.official_groups import (
    AdministeredClub,
    AdministeredGroupCard,
    AdministeredGroupPage,
    AdministeredGroups,
    SavedSettings,
)
from app.modules.groups.application.views import (
    ClubCard,
    EditedGroup,
    GroupAtClub,
    GroupPage,
    GroupRow,
    HomeClubResults,
    JoinSearchResults,
    LinkedGroup,
    MemberRow,
    MyGroup,
    NamedClub,
    RequestCard,
)
from app.modules.groups.domain.join_search import ReadAs
from app.modules.groups.domain.link import group_link
from app.modules.groups.domain.monogram import MONOGRAM_COLOURS, Monogram
from app.modules.groups.domain.ports import GroupFace
from app.modules.groups.domain.value_objects import (
    GroupKind,
    GroupRelation,
    JoinPolicy,
)

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

    @classmethod
    def from_view(cls, monogram: Monogram) -> "MonogramSchema":
        return cls(letters=monogram.letters, colour=monogram.colour)


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
    kind: GroupKind = Field(
        description=(
            "`PLAYER` — a player's own group, with an Owner. `OFFICIAL` — a "
            "club's, one per WhatsApp group, run by one of its Administrators: "
            "**no Owner**, and its sports are the ones it declares."
        )
    )
    name: str
    monogram: MonogramSchema
    sports: list[Sport] = Field(
        description=(
            "The sport dots, in the registry's order. **A player group's**: each "
            "sport **at least two** members hold a Skill rating in, read when the "
            "group is read — a rating earned or a member leaving moves them on "
            "the next read. **An official group's**: the sports it declares."
        )
    )
    member_count: int = Field(
        description=(
            "Every Group member — a player group's Owner, and the Administrator "
            "who joined an official group as a player, included. The same for "
            "every reader."
        )
    )

    @staticmethod
    def fields_of(row: GroupRow) -> dict:
        return {
            "id": row.id,
            "kind": row.kind,
            "name": row.name,
            "monogram": MonogramSchema.from_view(row.monogram),
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
    owner_nickname: str | None = Field(
        description=(
            "The Owner's **whole nickname** — who answers a request, for the "
            "*approves joins* line. **Nothing is cut from it, here or by a "
            "client**, and it is never written with an @: a sentence naming "
            "somebody uses the whole nickname (`docs/adr/0199` §1), so the line "
            "reads *karol.n approves joins* and the row truncates it as it "
            "truncates any line. `null` for an account that can no longer be "
            "named — and **always `null` on an official group**, which has no "
            "Owner: its line names `administrator_nickname`."
        )
    )
    administrator_nickname: str | None = Field(
        description=(
            "**An official group's** *approves joins* line: the Administrator "
            "running it now, by **their nickname** — and by the name their club "
            "typed for them only until they have one, for an Administrator who "
            "has never played (`docs/adr/0199` §4): *Administrator marta.w "
            "approves joins*, or *Administrator Marta Wójcik approves joins*. "
            "Cut by nobody, as `owner_nickname` is. `null` while nobody runs "
            "it, and **always `null` on a player group**, whose line names "
            "`owner_nickname`."
        )
    )
    is_administrator: bool = Field(
        description=(
            "Whether **the reader** runs this official group. Their tap is "
            "**Join**, never *Ask to join*: they are admitted at once whatever "
            "`join_policy` says — they would otherwise be asking themselves. "
            "Always `false` on a player group."
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
            owner_nickname=group.owner_nickname,
            relation=group.relation,
            administrator_nickname=group.administrator_nickname,
            is_administrator=group.is_administrator,
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
    """A member's face — **a nickname and a photograph, and nothing else**."""

    player_id: UUID
    nickname: str | None = Field(
        description=(
            "Their nickname, whole and never with an @ (`docs/adr/0199` §1). "
            "`null` for an account that can no longer be named — the member "
            "keeps their seat."
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

        fields: dict = {"player_id": face.player_id, "nickname": face.nickname}
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
    is_owner: bool = Field(
        description=(
            "Whether the reader is the group's Owner. Always `false` on an "
            "official group, which has none."
        )
    )
    declared_sports: list[Sport] = Field(
        OMITTED,
        description=(
            "**An official group's** declared sports, in the registry's order — "
            "what it plays, so the sport filter narrows to the ones the reader "
            "is rated in among these, and a reader rated in none of them is "
            "shown what to add. **Omitted on a player group**, which plays "
            "whatever its members are rated in."
        ),
    )
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
            "joined first. A block hides nobody here, as it hides nobody in the "
            "list it opens. Empty for a reader alone (`member_count` 1), whose "
            "row draws their own face. `member_count` is the group's, so its "
            "*+N* counts everybody."
        )
    )
    administrator_nickname: str | None = Field(
        description=(
            "**An official group's** *approves joins* line, as a club's card "
            "says it: the Administrator running it now, by their nickname — or "
            "by the name their club typed, for one who has never played "
            "(`docs/adr/0199` §4). "
            "**`null` while it needs an administrator** — the line then names "
            "the home club, *Ogrody 33 approves joins*, and requests wait for a "
            "handover — and **always `null` on a player group**, whose line "
            "names its Owner."
        )
    )
    is_administrator: bool = Field(
        description=(
            "Whether **the reader** runs this official group — who joined it as "
            "a player: *you approve joins*, answered from the administrator "
            "profile. Always `false` on a player group."
        )
    )

    @classmethod
    def from_view(cls, page: GroupPage, *, public_site: str) -> "GroupResponse":
        declared: dict = (
            {"declared_sports": list(page.row.sports)}
            if page.row.kind is GroupKind.OFFICIAL
            else {}
        )
        return cls(
            **GroupRowSchema.fields_of(page.row),
            **declared,
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
            administrator_nickname=page.administrator_nickname,
            is_administrator=page.is_administrator,
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
    """One row of Members, for one sport — *Padel 2,71 · 92 Very high*."""

    level: float = Field(
        description=(
            "Their Level in the sport asked for, as RacketSkill published it. "
            "Always present: somebody not rated in it is not listed."
        )
    )
    player_score: int = Field(
        ge=0,
        le=100,
        description=(
            "Their **Player reliability** in points, 0–100 — the figure their "
            "record prints. **Always present**: everyone starts at 100, so a "
            "member nothing has happened to reads `100`."
        ),
    )
    reliability_band: ReliabilityBand = Field(
        description=(
            "The word under that figure — `VERY_HIGH` 90–100, `HIGH` 75–89, "
            "`MEDIUM` 50–74, `LOW` below 50 — the same code their record "
            "serves. **Draw the word from this**, never from thresholds of your "
            "own."
        ),
    )
    is_owner: bool = Field(
        description=(
            "Whether they own the group — the row the **admin** tag is drawn on "
            "in a player group."
        )
    )
    is_administrator: bool = Field(
        description=(
            "Whether they run this **official** group as its Administrator, and "
            "joined it as a player — the row the **admin** tag is drawn on in an "
            "official group, second after the reader as an Owner is. Always "
            "`false` on a player group."
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
            "is_administrator": row.is_administrator,
            "joined_at": row.joined_at,
            "player_score": row.reliability.points,
            "reliability_band": row.reliability.band,
        }
        return cls(**fields)


class GroupMembersResponse(BaseModel):
    sport: Sport = Field(description="The sport the list was asked for.")
    members: list[GroupMemberSchema] = Field(
        description=(
            "**Only the members rated in `sport`**: the reader first, then the "
            "Owner — or the Administrator running an official group, once they "
            "joined it as a player — then everybody else **newest joined "
            "first**. **A block hides nobody here**, either way round. Empty "
            "when nobody in the group is rated in it."
        )
    )


# --------------------------------------------------------------------------- #
# The administrator surface
# --------------------------------------------------------------------------- #


class _OfficialGroupFields(BaseModel):
    """The four facts an Administrator gives an official group — at creation,
    and all four again on every settings save (``docs/adr/0183`` §3)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description=(
            "*Same name as the WhatsApp group*: trimmed, runs of whitespace "
            "collapsed, then 1–40 characters. Refused with `group_name_invalid`, "
            "`details.field` `name`."
        )
    )
    join_policy: JoinPolicy = Field(
        description=(
            "`ANYONE` or `PEOPLE_I_APPROVE`. **Switching to `ANYONE` admits "
            "everybody waiting at once.**"
        )
    )
    whatsapp_size: int = Field(
        description=(
            "How many people the WhatsApp group has — **required**, a whole "
            "number from 2 to 1024. It limits nothing: more players than this "
            "is allowed and honest. Refused with `whatsapp_size_invalid`, "
            "`details.field` `whatsapp_size`."
        )
    )
    sports: list[Sport] = Field(
        description=(
            "What the group plays — **required**, and **only the club's**. "
            "Ticking one twice is ticking it. Refused with "
            "`group_sports_required` for none, or `sport_not_offered_by_club` "
            "with the sport in `details.sport` — `details.field` `sports` either "
            "way."
        )
    )


class CreateOfficialGroupRequest(_OfficialGroupFields):
    """*New official group*. **The home club is not asked**: it is the club in
    the path, fixed."""


class OfficialGroupSettingsRequest(_OfficialGroupFields):
    """An official group's settings, **all four as the settings screen holds
    them**, recorded together or not at all."""


class OfficialGroupClubSchema(BaseModel):
    """The club an administrator acts for."""

    id: UUID
    name: str
    sports: list[Sport] = Field(
        description=(
            "What the club offers, in the registry's order — **the sports an "
            "official group may declare**, so the form offers exactly these."
        )
    )

    @classmethod
    def from_view(cls, club: AdministeredClub) -> "OfficialGroupClubSchema":
        return cls(id=club.id, name=club.name, sports=list(club.sports))


class AdministeredGroupCardSchema(GroupRowSchema):
    """A card on the administrator's Groups tab. `sports` are the declared
    dots; `member_count` is *N members*."""

    waiting_count: int = Field(
        description=(
            "How many Join requests are waiting — the amber *N waiting*. `0` "
            "when nobody is."
        )
    )
    home_club: ClubNameSchema

    @classmethod
    def from_view(cls, card: AdministeredGroupCard) -> "AdministeredGroupCardSchema":
        return cls(
            **GroupRowSchema.fields_of(card.row),
            waiting_count=card.waiting_count,
            home_club=ClubNameSchema.from_view(card.home_club),
        )


class AdministeredGroupsResponse(BaseModel):
    club: OfficialGroupClubSchema
    groups: list[AdministeredGroupCardSchema] = Field(
        description=(
            "**The official groups this administrator runs** at this club, "
            "newest created first — never a colleague's. Empty before the first: "
            "*No official groups yet*."
        )
    )

    @classmethod
    def from_view(cls, groups: AdministeredGroups) -> "AdministeredGroupsResponse":
        return cls(
            club=OfficialGroupClubSchema.from_view(groups.club),
            groups=[
                AdministeredGroupCardSchema.from_view(card) for card in groups.groups
            ],
        )


class GroupPlayerSchema(GroupPersonSchema):
    """One player on an official group's page — rows are not tappable, and
    nobody can be removed."""

    joined_at: datetime = Field(
        description=(
            "When they joined — this stay. The app prints *this week* within "
            "seven days, and the date after."
        )
    )


class AdministeredGroupResponse(GroupRowSchema):
    """An official group as the administrator running it opens it — and what
    its settings hold. `member_count` is *N players*."""

    home_club: OfficialGroupClubSchema
    link: str = Field(
        description=(
            "The Group link to post into the WhatsApp group: the public site's "
            "address, `/join/` and the group's code. **It never changes** — not "
            "on a rename, a policy change or a handover."
        )
    )
    join_policy: JoinPolicy
    whatsapp_size: int = Field(description="How many people the WhatsApp group has.")
    players: list[GroupPlayerSchema] = Field(
        description=(
            "Every player, **newest joined first** — the Administrator too, if "
            "they joined as a player. A block hides nobody here, as it hides "
            "nobody in a Members list; `member_count` is the group's."
        )
    )
    requests: list[JoinRequestSchema] = Field(
        description=(
            "*Want to join · N*: everybody waiting, in the order they asked, "
            "each with every sport they are rated in and its Level. Empty when "
            "nobody is."
        )
    )

    @classmethod
    def from_view(
        cls, page: AdministeredGroupPage, *, public_site: str
    ) -> "AdministeredGroupResponse":
        return cls(
            **GroupRowSchema.fields_of(page.row),
            home_club=OfficialGroupClubSchema.from_view(page.home_club),
            link=group_link(public_site, page.code),
            join_policy=page.join_policy,
            whatsapp_size=page.whatsapp_size,
            players=[
                GroupPlayerSchema(
                    **GroupPersonSchema.fields_of(player.face),
                    joined_at=player.joined_at,
                )
                for player in page.players
            ],
            requests=[JoinRequestSchema.from_card(card) for card in page.requests],
        )


class SavedSettingsResponse(BaseModel):
    """The group as its settings left it, and who the save let in."""

    group: AdministeredGroupResponse
    admitted: list[GroupPersonSchema] = Field(
        description=(
            "Everybody the switch to `ANYONE` admitted, **in the order they "
            "asked**. Empty for every other save."
        )
    )

    @classmethod
    def from_view(
        cls, saved: SavedSettings, *, public_site: str
    ) -> "SavedSettingsResponse":
        return cls(
            group=AdministeredGroupResponse.from_view(
                saved.page, public_site=public_site
            ),
            admitted=[GroupPersonSchema.from_view(face) for face in saved.admitted],
        )


# --------------------------------------------------------------------------- #
# The club surface: its Groups table and the handover (#510)
# --------------------------------------------------------------------------- #


class ClubGroupAdministratorSchema(BaseModel):
    """The Administrator running a group, as the club's own tables name them."""

    id: UUID = Field(
        description=(
            "The administratorship — the `id` of their row on the Administrators "
            "table, and what a handover names."
        )
    )
    name: str = Field(
        description=(
            "**The name the club gave them**, whole — the one its Administrators "
            "table prints beside the same person."
        )
    )

    @classmethod
    def from_view(
        cls, runner: ClubGroupAdministrator
    ) -> "ClubGroupAdministratorSchema":
        return cls(id=runner.id, name=runner.name)


class ClubGroupSchema(BaseModel):
    """One row of the club's Groups table: an official group at the club."""

    id: UUID
    name: str
    monogram: MonogramSchema
    administrator: ClubGroupAdministratorSchema | None = Field(
        description=(
            "Who runs it now. **`null` while it needs an administrator** — the "
            "club removed whoever ran it, and nobody has been handed it: players "
            "read *[club] approves joins* and its requests wait, until a "
            "handover."
        )
    )
    member_count: int = Field(
        description=(
            "*Players*: every Group member — an Administrator who joined it as a "
            "player included. **The same number the group page shows**, whoever "
            "reads it."
        )
    )
    waiting_count: int = Field(
        description=(
            "How many Join requests are waiting — the amber *N waiting*. `0` "
            "when nobody is."
        )
    )
    whatsapp_size: int = Field(
        description="How many people the WhatsApp group it mirrors has — *of 48*."
    )
    whatsapp_percent: int = Field(
        description=(
            "*From WhatsApp*: `member_count` over `whatsapp_size`, as a whole "
            "percent rounded half up — *11 of 48 · 23%*. **Never capped**: more "
            "players than the WhatsApp group has is the real figure, *52 of 48 · "
            "108%*, and the bar is drawn full."
        )
    )
    games: int = Field(
        description=(
            "How many games **were booked in the group** — every game its deck "
            "filled into a booking at a court — never a game two of its members "
            "arranged elsewhere."
        )
    )

    @classmethod
    def from_view(cls, row: ClubGroupRow) -> "ClubGroupSchema":
        return cls(
            id=row.id,
            name=row.name,
            monogram=MonogramSchema.from_view(row.monogram),
            administrator=(
                None
                if row.administrator is None
                else ClubGroupAdministratorSchema.from_view(row.administrator)
            ),
            member_count=row.member_count,
            waiting_count=row.waiting_count,
            whatsapp_size=row.whatsapp_size,
            whatsapp_percent=row.whatsapp_percent,
            games=row.games,
        )


class ClubGroupsResponse(BaseModel):
    groups: list[ClubGroupSchema] = Field(
        description=(
            "**Every official group at the club**, whoever runs it or nobody, by "
            "name. A player group whose home club this is is not the club's, and "
            "is never here. Empty before an Administrator makes the first."
        )
    )


class ClubJoinRequestSchema(BaseModel):
    """A Join request as the club answers it — club 20's card without the
    photograph: who is asking, by their nickname, and what they play
    (``docs/adr/0199``, #725). ``player_id`` is the id to approve or decline.
    **No Player Score**, as everywhere a request is drawn, and **no
    photograph**, which the club website draws nowhere."""

    player_id: UUID
    nickname: str | None = Field(
        description=(
            "Their nickname, whole (docs/adr/0199 §5) — *ania.k*. `null` for an "
            "account that can no longer be named, which reads as *A player* — "
            "the request still waits."
        )
    )
    levels: list[SportLevelSchema] = Field(
        description=(
            "**Every sport they are rated in**, in the registry's order, each "
            "with its Level — *Padel 2,44 · Tennis 2,60*. Empty for somebody "
            "rated in nothing."
        )
    )

    @classmethod
    def from_card(cls, card: RequestCard) -> "ClubJoinRequestSchema":
        return cls(
            player_id=card.face.player_id,
            nickname=card.face.nickname,
            levels=[
                SportLevelSchema(sport=row.sport, level=row.level)
                for row in card.levels
            ],
        )


class ClubJoinRequestsResponse(BaseModel):
    requests: list[ClubJoinRequestSchema] = Field(
        description=(
            "Everybody waiting to be let in, **in the order they asked** — "
            "*Want to join · N*, the same queue the administrator who runs it "
            "answers in the app. Empty when nobody is waiting."
        )
    )


class HandoversSeenRequest(BaseModel):
    """The groups the sheet told the Administrator about (``docs/adr/0192``)."""

    group_ids: list[UUID] = Field(
        min_length=1,
        max_length=100,
        description=(
            "The `group_id` of each handover the sheet named, from "
            "`/users/me`'s `profiles.handovers`. A group handed on meanwhile, "
            "told about already or not theirs is stepped over."
        ),
    )


class HandOverRequest(BaseModel):
    """*Hand over*: who the club chose."""

    administrator_id: UUID = Field(
        description=(
            "An **active** Administrator of the club — the `id` of an `ACTIVE` "
            "row on the Administrators table. Anybody else is "
            "`409 administrator_not_active`."
        )
    )


# --------------------------------------------------------------------------- #
# The public surface
# --------------------------------------------------------------------------- #


class LinkedGroupClubSchema(BaseModel):
    """Where the group plays, as the page's line under its name."""

    name: str
    district: str


class LinkedGroupResponse(BaseModel):
    """A group as its link's page draws it for somebody who has not signed in —
    and the preview a messenger draws from that page (``docs/adr/0187`` §4).
    **The least that page needs, and nobody in the group**: no member, Owner or
    administrator is named, counted apart or pictured (§5)."""

    name: str
    monogram: MonogramSchema
    club: LinkedGroupClubSchema
    sports: list[Sport] = Field(
        description=(
            "The sport dots, in the registry's order, by the rule every surface "
            "draws them by. **A player group's**: each sport **at least two** "
            "members hold a Skill rating in, read now. **An official group's**: "
            "the sports it declares."
        )
    )
    member_count: int = Field(
        description="How many are in it — the same count the app draws."
    )

    @classmethod
    def from_view(cls, group: LinkedGroup) -> "LinkedGroupResponse":
        return cls(
            name=group.row.name,
            monogram=MonogramSchema.from_view(group.row.monogram),
            club=LinkedGroupClubSchema(
                name=group.club_name, district=group.club_district
            ),
            sports=list(group.row.sports),
            member_count=group.row.member_count,
        )
