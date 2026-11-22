"""Wire schemas for the people rows (#793, #794, #795, #796, #812;
``docs/adr/0204`` §12, ``docs/adr/0205`` §6).

**The reader is never in a body**, and every relation is the reader's own —
the one wire vocabulary every face carries, Friends' ``FriendRelation``. What a
tile says in words (*Joined 2 days ago*, *Padel 2,35*) is the phone's, drawn
from the figures here (the words §31.7).
"""

from __future__ import annotations

import base64
import binascii
import math
from datetime import datetime, timedelta, timezone
from uuid import UUID

from pydantic import BaseModel, Field

from app.kernel import Sport, instant
from app.modules.discovery.application.new_in_raketa import (
    JoinerCard,
    NewInRaketaPage,
    NewInRaketaRow,
)
from app.modules.discovery.application.same_level import (
    SameLevelCard,
    SameLevelPage,
    SameLevelRow,
)
from app.modules.discovery.application.same_vibe import (
    SameVibeCard,
    SameVibePage,
    SameVibeRow,
)
from app.modules.discovery.domain.errors import (
    NotANewInRaketaPage,
    NotASameLevelPage,
    NotASameVibePage,
)
from app.modules.discovery.domain.new_in_raketa import JoinerKey
from app.modules.discovery.domain.rest import A_REPORT, OnScreenRow
from app.modules.discovery.domain.same_level import Comparison, SameLevelKey
from app.modules.discovery.domain.same_vibe import VibeKey
from app.modules.discovery.domain.totals import COUNTED_UP_TO
from app.modules.friends.domain.relation import FriendRelation

_EPOCH = instant(datetime(1970, 1, 1, tzinfo=timezone.utc))

#: What every row's ``total`` says after who it counts.
_A_TOTAL = (
    " — each person once, under the row's own exclusions — **counted up to "
    "100**: 100 reads *100 or more*, drawn *99+*. The line's count and *See all "
    "N ›*: who there is to explore, never how many are good matches. `0` with "
    "an empty row."
)


def cursor_of(key: JoinerKey) -> str:
    """A card's key as a cursor: *joined* in microseconds and the id,
    dot-separated, base64url — opaque to the phone."""

    delta = key.joined_at - _EPOCH
    micros = (delta.days * 86_400 + delta.seconds) * 1_000_000 + delta.microseconds
    written = f"{micros}.{key.player_id.hex}"
    return base64.urlsafe_b64encode(written.encode()).decode().rstrip("=")


def key_of(cursor: str) -> JoinerKey:
    """The key a cursor names — :class:`NotANewInRaketaPage` for one this server
    never wrote."""

    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        micros, player = base64.urlsafe_b64decode(padded.encode()).decode().split(".")
        return JoinerKey(
            joined_at=instant(_EPOCH + timedelta(microseconds=int(micros))),
            player_id=UUID(hex=player),
        )
    except (ValueError, OverflowError, UnicodeDecodeError, binascii.Error) as error:
        raise NotANewInRaketaPage() from error


class NewInRaketaSportSchema(BaseModel):
    sport: Sport
    level: float = Field(
        description="Their published Level in the sport — *Padel 2,35*."
    )


class NewInRaketaPlayerSchema(BaseModel):
    """One New in Raketa tile."""

    player_id: UUID
    nickname: str = Field(description="Whole, never with an @ (docs/adr/0199 §1).")
    photo_id: UUID | None = Field(
        description="Their first photograph; `null` draws their court poster."
    )
    photo_url: str | None = Field(
        description="A short-lived signed link to it, minted for this response."
    )
    joined_at: datetime = Field(
        description="When they finished sign-up — the profile commit."
    )
    days_since_joined: int = Field(
        ge=0,
        description=(
            "Warsaw days since they joined: `0` is *Joined today*, `1` *Joined "
            "yesterday*, 2–6 *Joined {n} days ago*, 7–13 *Joined last week*, "
            "then *Joined {n} weeks ago* (days ÷ 7, at most 4)."
        ),
    )
    sports: list[NewInRaketaSportSchema] = Field(
        description=(
            "Every sport they hold a level in, in the sports' own order — "
            "**empty** for a player with no level, whose tile shows no sport "
            "line."
        )
    )
    relation: FriendRelation = Field(
        description=(
            "Your relation to them — the round friend button: `NONE` **+**, "
            "`SENT` **…**, `FRIEND` **✓**, `ASKED_YOU` the envelope. A request "
            "is named by their `player_id` on every friends route. Send one "
            "from this row with `made_from` `NEW_PLAYERS`."
        )
    )

    @classmethod
    def of(cls, card: JoinerCard) -> "NewInRaketaPlayerSchema":
        return cls(
            player_id=card.player_id,
            nickname=card.nickname,
            photo_id=card.photo_id,
            photo_url=card.photo_url,
            joined_at=card.joined_at,
            days_since_joined=card.days_since_joined,
            sports=[
                NewInRaketaSportSchema(sport=level.sport, level=level.level)
                for level in card.levels
            ],
            relation=FriendRelation(card.relation.value),
        )


class NewInRaketaResponse(BaseModel):
    players: list[NewInRaketaPlayerSchema] = Field(
        description=(
            "Up to 10: the 10 newest of the last 30 days, those you aren't "
            "connected with first (someone who asked you among them), then "
            "those you sent a request to, then your friends — newest first "
            "within each. **Empty hides the row.**"
        )
    )
    total: int = Field(
        ge=0,
        le=COUNTED_UP_TO,
        description="How many the row could show: everybody who joined in the "
        "last 30 days" + _A_TOTAL,
    )

    @classmethod
    def of(cls, row: NewInRaketaRow) -> "NewInRaketaResponse":
        return cls(
            players=[NewInRaketaPlayerSchema.of(card) for card in row.cards],
            total=row.total,
        )


class NewInRaketaPageResponse(BaseModel):
    players: list[NewInRaketaPlayerSchema] = Field(
        description=(
            "Up to 20 players who joined in the last 30 days, newest first, friends "
            "where they fall — with `sport`, only those holding a level in it. "
            "Empty with a sport: *Nobody new plays squash yet*."
        )
    )
    next: str | None = Field(
        description=(
            "The cursor the next page is read `after`; `null` on the last page."
        )
    )
    sports: list[Sport] = Field(
        description=(
            "Every sport at least one of them holds a level in, in the sports' "
            "own order — the pill's chips beside *All*."
        )
    )

    @classmethod
    def of(cls, page: NewInRaketaPage) -> "NewInRaketaPageResponse":
        return cls(
            players=[NewInRaketaPlayerSchema.of(card) for card in page.cards],
            next=None if page.next is None else cursor_of(page.next),
            sports=list(page.sports),
        )


# --------------------------------------------------------------------------- #
# Same competitive level players (#794)
# --------------------------------------------------------------------------- #


def same_level_cursor_of(key: SameLevelKey) -> str:
    """A card's key as a cursor: the %, the gap to a millionth and the id,
    colon-separated, base64url — opaque to the phone."""

    written = f"{key.percent_even}:{key.distance!r}:{key.player_id.hex}"
    return base64.urlsafe_b64encode(written.encode()).decode().rstrip("=")


def same_level_key_of(cursor: str) -> SameLevelKey:
    """The key a cursor names — :class:`NotASameLevelPage` for one this server
    never wrote."""

    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        pct, distance, player = (
            base64.urlsafe_b64decode(padded.encode()).decode().split(":")
        )
        gap = float(distance)
        if not math.isfinite(gap) or gap < 0:
            raise ValueError(f"no card is {distance} away")
        return SameLevelKey(
            percent_even=int(pct), distance=gap, player_id=UUID(hex=player)
        )
    except (ValueError, UnicodeDecodeError, binascii.Error) as error:
        raise NotASameLevelPage() from error


class LevelBandSchema(BaseModel):
    """A band as the rating published it with the Level — the comparison
    bar's bold name. Its edges travel with it; never derived from a level."""

    name: str = Field(description="*Established* — RacketSkill's own word.")
    lower: float
    upper: float


class SameLevelSportSchema(BaseModel):
    """You and them in one sport you both hold a level in."""

    sport: Sport
    your_level: float = Field(description="Your Level in the sport — *You 2,71*.")
    their_level: float = Field(description="Theirs — *zofia.b 2,69*.")
    percent_even: int = Field(
        ge=0,
        le=100,
        description=(
            "How even a game between you two would be — the app's Forecast with "
            "one player a side, the figure a game card prints: green at 70 and "
            "above, amber 55–69, red below 55; the word under it is always "
            "*EVEN*. It falls with the gap and with how unsure the app is of "
            "either level, and tops out at 96."
        ),
    )
    level_gap: float = Field(
        description=(
            "Their level less yours, to the hundredth, signed: `-0.02` is *0,02 "
            "below you*, `0.09` *0,09 above you*, `0` *Same level*. A level gap, "
            "never a row's **gap** (a place after the fresh good matches)."
        )
    )
    your_band: LevelBandSchema = Field(
        description="Your band in the sport — the bar's name in bold."
    )

    @classmethod
    def of(cls, comparison: Comparison) -> "SameLevelSportSchema":
        return cls(
            sport=comparison.sport,
            your_level=comparison.your_level,
            their_level=comparison.their_level,
            percent_even=comparison.percent_even,
            level_gap=round(comparison.level_gap, 2),
            your_band=LevelBandSchema(
                name=comparison.your_band.name,
                lower=comparison.your_band.lower,
                upper=comparison.your_band.upper,
            ),
        )


class SameLevelPlayerSchema(BaseModel):
    """One *Same competitive level* card."""

    player_id: UUID
    nickname: str = Field(description="Whole, never with an @ (docs/adr/0199 §1).")
    photo_id: UUID | None = Field(
        description="Their first photograph; `null` draws their court poster."
    )
    photo_url: str | None = Field(
        description="A short-lived signed link to it, minted for this response."
    )
    shown: SameLevelSportSchema = Field(
        description=(
            "The sport the card shows: the one where you two are evenest — or, "
            "on a See all page asked for a sport, that one."
        )
    )
    sports: list[SameLevelSportSchema] = Field(
        description=(
            "**Every** sport you share, most even first — the comparison sheet's "
            "blocks, so it needs no read. *N sports ›* when there is more than "
            "one."
        )
    )
    relation: FriendRelation = Field(
        description=(
            "Your relation to them — the round friend button: `NONE` **+**, "
            "`SENT` **…**, `FRIEND` **✓**, `ASKED_YOU` the envelope. A request "
            "is named by their `player_id` on every friends route. Send one "
            "from this row with `made_from` `SAME_LEVEL` and the card's sport."
        )
    )

    @classmethod
    def of(cls, card: SameLevelCard) -> "SameLevelPlayerSchema":
        return cls(
            player_id=card.player_id,
            nickname=card.nickname,
            photo_id=card.photo_id,
            photo_url=card.photo_url,
            shown=SameLevelSportSchema.of(card.shown),
            sports=[SameLevelSportSchema.of(one) for one in card.comparisons],
            relation=FriendRelation(card.relation.value),
        )


class SameLevelResponse(BaseModel):
    players: list[SameLevelPlayerSchema] = Field(
        description=(
            "Up to 10: **fresh** good matches first — 70% even or more, neither "
            "your friend nor somebody you asked — best % first; then the "
            "**gaps** at the right — your friends, those you asked and weaker "
            "matches — best % first. Worked out on every read, so a new fresh "
            "player takes the weakest gap's place. **Empty hides the row**: "
            "you hold no level anywhere, or nobody shares a sport with you."
        )
    )
    total: int = Field(
        ge=0,
        le=COUNTED_UP_TO,
        description="How many the row could show: everybody holding a level in "
        "any sport you hold one in" + _A_TOTAL,
    )

    @classmethod
    def of(cls, row: SameLevelRow) -> "SameLevelResponse":
        return cls(
            players=[SameLevelPlayerSchema.of(card) for card in row.cards],
            total=row.total,
        )


class SameLevelPageResponse(BaseModel):
    players: list[SameLevelPlayerSchema] = Field(
        description=(
            "Up to 20, best % first, friends where they fall — with `sport`, "
            "everybody holding a level in it, compared there."
        )
    )
    next: str | None = Field(
        description=(
            "The cursor the next page is read `after`; `null` on the last page."
        )
    )
    sports: list[Sport] = Field(
        description=(
            "Every sport you share with somebody, in the sports' own order — the "
            "pill's chips beside *All*."
        )
    )

    @classmethod
    def of(cls, page: SameLevelPage) -> "SameLevelPageResponse":
        return cls(
            players=[SameLevelPlayerSchema.of(card) for card in page.cards],
            next=None if page.next is None else same_level_cursor_of(page.next),
            sports=list(page.sports),
        )


# --------------------------------------------------------------------------- #
# Same vibe players (#795)
# --------------------------------------------------------------------------- #


def same_vibe_cursor_of(key: VibeKey) -> str:
    """A card's key as a cursor: the tags in common, theirs not shared and the
    id, colon-separated, base64url — opaque to the phone."""

    written = f"{key.in_common}:{key.not_shared}:{key.player_id.hex}"
    return base64.urlsafe_b64encode(written.encode()).decode().rstrip("=")


def same_vibe_key_of(cursor: str) -> VibeKey:
    """The key a cursor names — :class:`NotASameVibePage` for one this server
    never wrote."""

    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        in_common, not_shared, player = (
            base64.urlsafe_b64decode(padded.encode()).decode().split(":")
        )
        key = VibeKey(
            in_common=int(in_common),
            not_shared=int(not_shared),
            player_id=UUID(hex=player),
        )
        if key.in_common < 1 or key.not_shared < 0:
            raise ValueError(f"no card stands at {key!r}")
        return key
    except (ValueError, UnicodeDecodeError, binascii.Error) as error:
        raise NotASameVibePage() from error


class SameVibePlayerSchema(BaseModel):
    """One *Same vibe players* tile."""

    player_id: UUID
    nickname: str = Field(description="Whole, never with an @ (docs/adr/0199 §1).")
    photo_id: UUID | None = Field(
        description="Their first photograph; `null` draws their court poster."
    )
    photo_url: str | None = Field(
        description="A short-lived signed link to it, minted for this response."
    )
    vibe_percent: int = Field(
        ge=50,
        le=100,
        description=(
            "The **vibe %**, 1 − ½ⁿ for n shared tags, rounded: 50, 75, 88, 94, "
            "97, 98, 99, 100 for 1–8 — the white circle, *98%*. Every tag "
            "counts the same, and skill plays no part."
        ),
    )
    in_common: int = Field(
        ge=1,
        description=(
            "How many tags you both hold — *6 things in common*, *1 thing in common*."
        ),
    )
    shared_tags: list[str] = Field(
        description=(
            "The Social tag ids you both hold, in the vocabulary's own order — "
            "the green chips, as many whole as fit in three lines, then *+2 "
            "more*. The vibe sheet reads the player's record for all their "
            "tags, photos, intro and distance."
        )
    )
    relation: FriendRelation = Field(
        description=(
            "Your relation to them — the round friend button: `NONE` **+**, "
            "`SENT` **…**, `FRIEND` **✓**, `ASKED_YOU` the envelope. A request "
            "is named by their `player_id` on every friends route. Send one "
            "from this row with `made_from` `SAME_VIBE`."
        )
    )

    @classmethod
    def of(cls, card: SameVibeCard) -> "SameVibePlayerSchema":
        return cls(
            player_id=card.player_id,
            nickname=card.nickname,
            photo_id=card.photo_id,
            photo_url=card.photo_url,
            vibe_percent=card.vibe_percent,
            in_common=card.in_common,
            shared_tags=list(card.shared_tags),
            relation=FriendRelation(card.relation.value),
        )


class SameVibeResponse(BaseModel):
    players: list[SameVibePlayerSchema] = Field(
        description=(
            "Up to 10: **fresh** good matches first — 2 shared tags or more, "
            "neither your friend nor somebody you asked; somebody who asked "
            "you counts — most in common first; then the **gaps** at the right "
            "— your friends, those you asked and 1-tag matches — in the same "
            "order. Worked out on every read, so a new fresh player takes the "
            "weakest gap's place. **Empty hides the row.**"
        )
    )
    total: int = Field(
        ge=0,
        le=COUNTED_UP_TO,
        description="How many the row could show: everybody sharing at least "
        "one Social tag with you" + _A_TOTAL,
    )

    @classmethod
    def of(cls, row: SameVibeRow) -> "SameVibeResponse":
        return cls(
            players=[SameVibePlayerSchema.of(card) for card in row.cards],
            total=row.total,
        )


class SameVibePageResponse(BaseModel):
    players: list[SameVibePlayerSchema] = Field(
        description=(
            "Up to 20 who share a tag with you, most in common first, friends "
            "where they fall — with `sport`, only those holding a level in it."
        )
    )
    next: str | None = Field(
        description=(
            "The cursor the next page is read `after`; `null` on the last page."
        )
    )
    sports: list[Sport] = Field(
        description=(
            "Every sport at least one of them holds a level in, in the sports' "
            "own order — the pill's chips beside *All*."
        )
    )

    @classmethod
    def of(cls, page: SameVibePage) -> "SameVibePageResponse":
        return cls(
            players=[SameVibePlayerSchema.of(card) for card in page.cards],
            next=None if page.next is None else same_vibe_cursor_of(page.next),
            sports=list(page.sports),
        )


class OnScreenRequest(BaseModel):
    """The cards that came on screen in one row (#796)."""

    row: OnScreenRow = Field(
        description=(
            "The row they came on screen in — `SAME_LEVEL` or `SAME_VIBE`, each "
            "with its own count. New in Raketa and See all rest nobody, so are "
            "never reported."
        )
    )
    player_ids: list[UUID] = Field(
        min_length=1,
        max_length=A_REPORT,
        description=(
            "Each card at least half visible — the card's `player_id`. A card "
            "named twice, or reported again the same Warsaw day, counts once."
        ),
    )
