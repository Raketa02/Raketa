"""Wire schemas for the people rows (#793; ``docs/adr/0204`` §12).

**The reader is never in a body**, and every relation is the reader's own —
the one wire vocabulary every face carries, Friends' ``FriendRelation``. What a
tile says in words (*Joined 2 days ago*, *Padel 2,35*) is the phone's, drawn
from the figures here (the words §31.7).
"""

from __future__ import annotations

import base64
import binascii
from datetime import datetime, timedelta, timezone
from uuid import UUID

from pydantic import BaseModel, Field

from app.kernel import Sport, instant
from app.modules.discovery.application.new_in_raketa import (
    JoinerCard,
    NewInRaketaPage,
)
from app.modules.discovery.domain.errors import NotANewInRaketaPage
from app.modules.discovery.domain.new_in_raketa import JoinerKey
from app.modules.friends.domain.relation import FriendRelation

_EPOCH = instant(datetime(1970, 1, 1, tzinfo=timezone.utc))


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
