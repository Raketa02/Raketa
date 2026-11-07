"""The wire shapes of You › Account › **Notifications**, a phone's push token,
the recent notices and the bell's number (#549, #621; the screens A7.2, A9)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.notifications.application.reading import RecentNotice, RecentNotices
from app.modules.notifications.domain.notices import NoticeKind, Opens
from app.modules.notifications.domain.preferences import (
    NotificationChoice,
    NotificationPreferences,
)


class NotificationChoicesSchema(BaseModel):
    """The three notices a player chooses. Every other kind is always on, no
    choice, and not here."""

    you_complete_it: bool = Field(
        description=(
            "*You complete it* — a card needs only you. On until switched off; "
            "at most one a day, the rest bundled into it."
        )
    )
    challenges_for_you: bool = Field(
        description=(
            "*Challenges for you* — a member's post names you. On until switched "
            "off; at most three a day, the rest bundled into the third."
        )
    )
    fill_in_alerts: bool = Field(
        description=(
            "*Fill in alerts* — a booked game you fit needs one more. Off until "
            "switched on; at most three a day."
        )
    )

    @classmethod
    def from_preferences(
        cls, preferences: NotificationPreferences
    ) -> "NotificationChoicesSchema":
        # Each field is its choice's name, lower-cased.
        return cls(
            **{
                choice.value.lower(): preferences.wants(choice)
                for choice in NotificationChoice
            }
        )

    def as_choices(self) -> dict[NotificationChoice, bool]:
        return {
            choice: getattr(self, choice.value.lower()) for choice in NotificationChoice
        }


class PushDeviceRequest(BaseModel):
    token: str = Field(
        description=(
            "The phone's Expo push token — `ExponentPushToken[…]` or "
            "`ExpoPushToken[…]` — as the notifications library hands it out."
        ),
        max_length=255,
    )


class NoticeSchema(BaseModel):
    """One notice, in the words the phone was pushed — and where a tap opens."""

    notice_id: UUID
    kind: NoticeKind
    title: str
    body: str
    given_at: datetime = Field(
        description=(
            "When it was given — or when the day last bundled a notice into it, "
            "which is what moves it up the list."
        )
    )
    opens: Opens = Field(
        description=(
            "`BOOKING` — the booked game's details (`GET /bookings/{game_id}`); "
            "`PROPOSAL` — a game still filling, or one that did not "
            "(`GET /proposals/{game_id}`); `DECK` — the pool's deck in the "
            "sport and kind, with this card on top; `RESULT` — the booked "
            "game's result screen (`GET /bookings/{game_id}`): who turned up, "
            "and the score (#663); `HOME` — Home, for a notice about no game "
            "(*Get your level*, #727; a friend request, whose card is there, "
            "#745); `RECORD` — the record of `player_id`, a new friend; "
            "`QUESTIONNAIRE` — the questionnaire of `sport`, through the level "
            "pass and its usual return (`LEVEL_ASKED`, #749); `PICKER` — the "
            "Friends tab's picker of the group `pool_id` in `sport`, where "
            "`player_id` can be seated now (`LEVEL_GOT`, #749)."
        )
    )
    game_id: UUID | None = Field(
        description=(
            "The game it is about: its proposal's id, which its booking takes. "
            "`null` on a notice about no game — `GET_YOUR_LEVEL`, which opens "
            "`HOME` — and then `pool_id`, `sport` and `game_kind` are `null` "
            "too."
        )
    )
    pool_id: UUID | None = Field(
        description=(
            "The game's pool. On a `FRIEND_REQUEST`, the group it was asked from "
            "(a group's pool is filed under its id), or `null`; on a "
            "`LEVEL_GOT`, the group the ask was made from, whose picker it "
            "opens."
        )
    )
    sport: Sport | None = Field(
        description=(
            "The game's sport. On a notice about no game, the sport it names — "
            "a friend request's screen, or the level a `LEVEL_ASKED` asks for "
            "and a `LEVEL_GOT` says arrived — or `null`."
        )
    )
    game_kind: SearchMode | None
    player_id: UUID | None = Field(
        description=(
            "On a notice about no game that names somebody — `FRIEND_REQUEST`, "
            "who asked; `FRIENDS_MADE`, the new friend, whose record `RECORD` "
            "opens; `LEVEL_ASKED`, the friend who asked; `LEVEL_GOT`, the friend "
            "who got the level. `null` on every other notice."
        )
    )
    gathered: int = Field(
        description=(
            "How many more notices of its kind the day bundled into this one — "
            "told in its words, and pushed to nobody."
        )
    )
    new: bool = Field(
        description=(
            "It reached the list since you last opened it — given, or a notice "
            "bundled into it, which moved it up — and is not your own: one the "
            "bell counts, and a row to make stand out on this visit."
        )
    )
    your_own: bool = Field(
        description=(
            "About something you did yourself and saw happen — *It's a game!* "
            "for the yes that filled the game, or the seat you took. Born "
            "seen: listed, never counted on the bell, never pushed, and never "
            "to be shown as a banner."
        )
    )

    @classmethod
    def from_recent(cls, recent: RecentNotice) -> "NoticeSchema":
        notice = recent.notice
        return cls(
            notice_id=notice.notice_id,
            kind=NoticeKind(notice.kind),
            title=recent.words.title,
            body=recent.words.body,
            given_at=notice.given_at,
            opens=Opens(notice.opens),
            game_id=notice.game_id,
            pool_id=notice.pool_id,
            sport=notice.sport,
            game_kind=None
            if notice.game_kind is None
            else SearchMode(notice.game_kind),
            player_id=notice.person_named,
            gathered=notice.gathered,
            new=notice.new,
            your_own=notice.own,
        )


class RecentNoticesResponse(BaseModel):
    notices: list[NoticeSchema] = Field(description="The newest first.")
    new_count: int = Field(
        description=(
            "**The bell's number**: the notices that reached your list since you "
            "last opened it — given, or bundled into one and moving it up — "
            "never your own. Exact however many rows were asked for: the bell "
            "writes *99+* past 99. The same on every phone."
        )
    )
    last_opened_at: datetime | None = Field(
        description=(
            "When you last opened the list (`POST /players/me/notices/visit`), on "
            "any phone — `null` before the first time."
        )
    )

    @classmethod
    def from_recent(cls, recent: RecentNotices) -> "RecentNoticesResponse":
        return cls(
            notices=[NoticeSchema.from_recent(notice) for notice in recent.notices],
            new_count=recent.new_count,
            last_opened_at=recent.last_opened_at,
        )
