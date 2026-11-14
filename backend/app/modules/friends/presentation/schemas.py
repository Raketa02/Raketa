"""Wire schemas for the Friends context.

**The reader is never in a body** — it is the authenticated caller, always — and
**every response carries only the reader's own relations** (``docs/adr/0202``
§2): who the reader's friends are, whom the reader asked and who asked the
reader, and never anything between two other people.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.kernel import Sport, invariant
from app.modules.friends.application.reads import (
    Direction,
    Friend,
    FriendRequest,
    GroupToAddFrom,
)
from app.modules.friends.domain.friendship import Where
from app.modules.friends.domain.link import FriendLinkCode, friend_link_url
from app.modules.friends.domain.ports import FriendFace
from app.modules.friends.domain.relation import FriendRelation, RequestOrigin


class AskedFrom(StrEnum):
    """The screen a request is asked from. **Not a link**: a request by link is
    made by opening the link, never sent here."""

    MEMBERS = RequestOrigin.MEMBERS.value
    RECORD = RequestOrigin.RECORD.value
    RESULT = RequestOrigin.RESULT.value
    RANKING = RequestOrigin.RANKING.value
    NEW_PLAYERS = RequestOrigin.NEW_PLAYERS.value
    SAME_LEVEL = RequestOrigin.SAME_LEVEL.value
    SAME_VIBE = RequestOrigin.SAME_VIBE.value


class AskToBeFriendsRequest(BaseModel):
    player_id: UUID = Field(description="Who to ask. You are never sent.")
    made_from: AskedFrom = Field(
        description=(
            "Where **+ Add** or **Add friend** was pressed: a group's Members (or "
            "a face on one of its games), the player record, the result "
            "screen's *PLAYED WITH* card, or **the record opened from the "
            "Rankings page** — `RANKING`, with that page's `sport` (#773). Their "
            "Home card and notice then read *Found you in the padel ranking*, "
            "whether or not you share a group. From Home's **New in Raketa** "
            "row, or a record opened from it — `NEW_PLAYERS` (#793): their card "
            "and notice read *Found you among new players*. From Home's **Same "
            "competitive level players** row, or a record opened from it — "
            "`SAME_LEVEL`, with the card's `sport` (#794): their card and notice "
            "read *Your level in padel · 91% even*, today's %, or *Found you at "
            "your padel level* once either of you holds no level there. From "
            "Home's **Same vibe players** row, or a record opened from it — "
            "`SAME_VIBE` (#795): their card and notice read *6 things in common* "
            "(*1 thing in common*), counted when read, or *Found you through your "
            "tags* once you share none."
        )
    )
    group_id: UUID | None = Field(
        default=None,
        description=(
            "The group the screen showed — Members' group, or the game's — which "
            "their Home card names (*With you in Kazimierz crew*) while you are "
            "both in it. Omit it where the screen showed none; it is ignored "
            "with `RANKING`, `NEW_PLAYERS`, `SAME_LEVEL` and `SAME_VIBE`, whose "
            "screens show no group."
        ),
    )
    sport: Sport | None = Field(
        default=None,
        description=(
            "The sport the screen showed, whose Level the card prints beside your "
            "nickname (*Padel 3,40*). Omit it where the screen showed none; "
            "it is ignored with `NEW_PLAYERS` and `SAME_VIBE`, whose lines name "
            "no sport. "
            "**Required with `RANKING`** — it is the ranking the card names — "
            "**and with `SAME_LEVEL`**: it is the sport their line compares."
        ),
    )

    @model_validator(mode="after")
    def _a_ranking_names_its_sport(self) -> "AskToBeFriendsRequest":
        if self.made_from is AskedFrom.RANKING and self.sport is None:
            raise ValueError("a request made from the ranking names its sport")
        if self.made_from is AskedFrom.SAME_LEVEL and self.sport is None:
            raise ValueError(
                "a request made from Same competitive level names its sport"
            )
        return self

    def where(self) -> Where:
        return Where.pressed_on(
            RequestOrigin(self.made_from.value),
            group_id=self.group_id,
            sport=self.sport,
        )


class RelationResponse(BaseModel):
    relation: FriendRelation = Field(
        description=(
            "Your relation to them now: `SENT` once asked — *request sent*, for "
            "as long as the request stays open, whatever they do with it — or "
            "`FRIEND`, when they had asked you first and the requests crossed, "
            "or when you accepted."
        )
    )


class FriendSportSchema(BaseModel):
    sport: Sport
    level: float = Field(description="Their published Level in the sport.")
    band: str = Field(
        description=(
            "The Level band's published name (*Established*), RacketSkill's own "
            "word — the picker's *2,75 · established*. Never derived from "
            "`level`."
        )
    )


class FriendSchema(BaseModel):
    player_id: UUID
    nickname: str = Field(description="Whole, never with an @ (docs/adr/0199 §1).")
    photo_id: UUID | None = Field(
        description="Their first photograph; `null` with `photo_url` draws initials."
    )
    photo_url: str | None = Field(
        description="A short-lived signed link to it, minted for this response."
    )
    friends_since: datetime
    sports: list[FriendSportSchema] = Field(
        description=(
            "Every sport they are rated in, in the sports' own order — or, with "
            "`sport`, that one alone, and **empty** when they have no Level in "
            "it: *No padel level yet*."
        )
    )
    level_asked_in: list[Sport] = Field(
        description=(
            "Every sport **you** asked them to get a level in, answered or not, "
            "in the sports' own order — or, with `sport`, that one alone or "
            "nothing. On a greyed row it reads **Asked** in place of *Ask … to "
            "get a padel level*: you ask once per sport, ever. Only your own "
            "asks: nobody else's are on the wire."
        )
    )

    @classmethod
    def of(cls, friend: Friend) -> "FriendSchema":
        return cls(
            player_id=friend.player_id,
            nickname=friend.nickname,
            photo_id=friend.photo_id,
            photo_url=friend.photo_url,
            friends_since=friend.since,
            sports=[
                FriendSportSchema(sport=level.sport, level=level.level, band=level.band)
                for level in friend.levels
            ],
            level_asked_in=list(friend.level_asked_in),
        )


class FriendsResponse(BaseModel):
    sport: Sport | None = Field(description="The sport asked for, if one was.")
    friends: list[FriendSchema] = Field(
        description=(
            "**Your** friends, from every group. Without `sport`, by nickname "
            "(You › Friends); with it, highest Level in it first and anybody "
            "with no Level in it last (the picker). Empty when you have none: "
            "*No friends yet. Add them from your groups, or send your link.*"
        )
    )


class FriendRequestSchema(BaseModel):
    player_id: UUID
    nickname: str
    photo_id: UUID | None
    photo_url: str | None
    asked_at: datetime
    set_aside: bool = Field(
        description=(
            "On *Asked you*: you said **Not now** — it stays open, and **Accept** "
            "still answers it. Always `false` on *You asked*: whether they set "
            "yours aside is never said."
        )
    )

    @classmethod
    def of(cls, request: FriendRequest) -> "FriendRequestSchema":
        return cls(
            player_id=request.player_id,
            nickname=request.nickname,
            photo_id=request.photo_id,
            photo_url=request.photo_url,
            asked_at=request.asked_at,
            set_aside=request.set_aside,
        )


class FriendRequestsResponse(BaseModel):
    direction: Direction
    requests: list[FriendRequestSchema] = Field(
        description=(
            "Open requests, **newest first** — `ASKED_YOU`: made of you, set "
            "aside or not (*Asked you · n* counts them); `YOU_ASKED`: yours. "
            "An answered or cancelled request is in neither."
        )
    )


class GroupToAddFromSchema(BaseModel):
    group_id: UUID
    name: str
    member_count: int = Field(description="Everybody in it, you included.")
    to_add: int = Field(
        description=(
            "Members you could still ask: not you, not a friend, nobody with an "
            "open request either way, and nobody you blocked — *8 members · 2 "
            "to add*, *nobody to add* at 0."
        )
    )

    @classmethod
    def of(cls, group: GroupToAddFrom) -> "GroupToAddFromSchema":
        return cls(
            group_id=group.group_id,
            name=group.name,
            member_count=group.member_count,
            to_add=group.to_add,
        )


class GroupsToAddFromResponse(BaseModel):
    groups: list[GroupToAddFromSchema] = Field(
        description="Every group you are in, newest joined first."
    )


class AskForALevelRequest(BaseModel):
    """**Ask {nickname} to get a padel level**, on a greyed row of a group's
    picker (#749). The friend is the path's; you are never sent."""

    sport: Sport = Field(
        description="The picker's sport — the level they are asked to get."
    )
    group_id: UUID = Field(
        description=(
            "The group whose Friends tab the picker is on — one of yours. When "
            "they get the level, your notice opens this group's picker."
        )
    )


class FriendLinkResponse(BaseModel):
    """Your Friend link, as the Add friends sheet's *Not on Raketa yet?* card
    shows it (#748)."""

    code: str = Field(
        description=(
            "What follows `/f/`: eight letters and digits, random, shaped like a "
            "group's code. **The same on every read** until you take a New link."
        )
    )
    link: str = Field(
        description="`<public site>/f/<code>` — what **Copy** puts on the clipboard."
    )

    @classmethod
    def of(cls, code: FriendLinkCode, *, public_site: str) -> "FriendLinkResponse":
        return cls(code=code.value, link=friend_link_url(public_site, code))


class OpenedFriendLinkResponse(BaseModel):
    relation: FriendRelation = Field(
        description=(
            "Your relation to the link's owner once it is opened. `ASKED_YOU` — "
            "their request is on your Home, *Invited you to Raketa*: land there. "
            "`FRIEND` — you were friends already, or you had asked them and the "
            "requests crossed. `NONE` — the link is your own, and nothing "
            "happened."
        )
    )


class LinkedFriendResponse(BaseModel):
    """A Friend link's owner as the public site's `/f/<code>` page draws them for
    somebody who has not signed in — *{nickname} invited you to play on
    Raketa* — **and nothing else about them**."""

    nickname: str
    photo_url: str | None = Field(
        description=(
            "Their first photograph, a link that expires within minutes; `null` "
            "when they have none."
        )
    )

    @classmethod
    def of(cls, face: FriendFace) -> "LinkedFriendResponse":
        nickname = invariant(face.nickname, f"a link's page with no name: {face!r}")
        return cls(nickname=nickname, photo_url=face.photo_url)
