"""The wire shapes of You › Account › **Notifications**, a phone's push token,
and the recent notices (#549; the screens A7.2, A9)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.notifications.application.reading import RecentNotice
from app.modules.notifications.domain.notices import NoticeKind, Opens
from app.modules.notifications.domain.preferences import (
    NotificationChoice,
    NotificationPreferences,
)


class NotificationChoicesSchema(BaseModel):
    """The three notices a player chooses. The seven that are always on are
    no choice, and are not here."""

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
            "sport and kind, with this card on top."
        )
    )
    game_id: UUID = Field(
        description="The game it is about: its proposal's id, which its booking takes."
    )
    pool_id: UUID
    sport: Sport
    game_kind: SearchMode
    gathered: int = Field(
        description=(
            "How many more notices of its kind the day bundled into this one — "
            "told in its words, and pushed to nobody."
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
            game_kind=SearchMode(notice.game_kind),
            gathered=notice.gathered,
        )


class RecentNoticesResponse(BaseModel):
    notices: list[NoticeSchema] = Field(description="The newest first.")
