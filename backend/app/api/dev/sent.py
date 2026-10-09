"""A person's *Sent* pane: who was told what, without a second device
(``docs/adr/0194``; #594).

Three places a person is told something, read in one press:

- **The in-app notices** — the list behind the bell, read by the player's own
  route's use case (``ReadRecentNotices``), so each row is the one
  ``GET /api/v1/players/me/notices`` answers them.
- **The push each notice was given as** — ``NoticePushes``, the pusher's own,
  drawn from the notice's facts as the list is: what a phone registered when it
  was given was pushed, and, with none, what would have been — nothing for a
  notice of the player's own act (#621). ``phones`` counts the phones
  registered now. No seed account has one, and the player app registers none
  until push is switched on.
- **Their emails**, from the outgoing mail queue: what was queued for their
  address, whether it went, and a link to it in the dev stack's mail catcher
  (``MAIL_CATCHER_URL``) — searched by the Message-ID the mail worker sends it
  under, which is the queue row's id. The bodies are not read: the queue holds a
  link or a code until the send purges it, and this pane has no use for either.

**Not the recording push service**, which the ticket named. It would hold
nothing here: ``PushTheNotice`` asks the service nothing for a player with no
phone, so it is never asked about a seed account; ``local`` pushes through Expo
unless ``PUSH_PROVIDER`` says ``recording``; and what a recording remembers is
the process's, gone at the next reload. The pusher's own answer to *what is
this notice pushed as* is the same answer for any player, phone or none.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from datetime import datetime
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.dependencies import DbSession, SettingsDep
from app.api.dev.accounts import SeedAccountDep
from app.api.dev.dependencies import NoticePushesDep
from app.core.exception_handlers import ErrorResponse
from app.infrastructure.database.stored_time import (
    stored_instant,
    stored_instant_or_none,
)
from app.infrastructure.mail.mail_queue_model import MailQueueORM
from app.modules.notifications.application.reading import MOST_RECENT
from app.modules.notifications.presentation.dependencies import (
    NotificationPreferencesRepositoryDep,
    ReadRecentNoticesDep,
)
from app.modules.notifications.presentation.schemas import NoticeSchema

router = APIRouter(prefix="/as/{player_id}", tags=["dev"])


def in_the_mail_catcher(inbox: str, mail_id: UUID) -> str:
    """The mail catcher's search for the one email sent under this queue id —
    its Message-ID is ``<mail_id@…>``, and the catcher matches a part of one."""

    return f"{inbox}/search?{urlencode({'q': f'message-id:{mail_id}'})}"


class SentPush(BaseModel):
    title: str = Field(..., description="What the phone's system shows first.")
    body: str
    data: dict[str, str] = Field(
        ..., description="What a tap hands the app: the notice, and where it opens."
    )


class SentNotice(BaseModel):
    listed: NoticeSchema = Field(
        ...,
        description=(
            "As the bell lists it now — `GET /api/v1/players/me/notices`'s own "
            "row, `gathered` included."
        ),
    )
    pushed: SentPush | None = Field(
        ...,
        description=(
            "What it is pushed as — to each phone registered when it was "
            "given, and with none, what would have been: its words as given, "
            "before the day gathered anything into it, which pushes nobody. "
            "Drawn from its facts again now, as `listed` is, so a name changed "
            "since reads as it stands. `null` for a notice of their own act "
            "(`listed.your_own`), which is pushed to nobody."
        ),
    )


class SentEmail(BaseModel):
    mail_id: UUID = Field(
        ...,
        description="The queue row's id — the email's Message-ID is made of it.",
    )
    kind: str = Field(..., description="Which email: `payments.game_booked.player`.")
    subject: str
    queued_at: datetime
    sent_at: datetime | None = Field(
        ..., description="When the mail worker handed it to the relay. `null` until."
    )
    given_up_at: datetime | None = Field(
        ..., description="When the worker stopped retrying it. It was never sent."
    )
    attempts: int = Field(..., description="Failed sends so far.")
    last_error: str | None = Field(
        ..., description="The relay's account of the last failure."
    )
    in_the_mail_catcher: str | None = Field(
        ...,
        description=(
            "The mail catcher's page for it, once it was sent; `null` before — "
            "the catcher has nothing yet — and for one given up on."
        ),
    )


class SentResponse(BaseModel):
    email: str = Field(..., description="The address their emails are queued for.")
    phones: int = Field(
        ...,
        description=(
            "How many phones are registered to be pushed to now — not when "
            "each notice was given. 0 — every seed account — means no notice "
            "since the last phone went was pushed: each `pushed` is what would "
            "have been."
        ),
    )
    notices: list[SentNotice] = Field(
        ..., description=f"The newest first, at most {MOST_RECENT}."
    )
    emails: list[SentEmail] = Field(
        ..., description=f"The newest first, at most {MOST_RECENT}."
    )


_REFUSED: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": "`not_a_seed_account` — not an account the seed created.",
    },
}


@router.get(
    "/sent",
    response_model=SentResponse,
    status_code=status.HTTP_200_OK,
    responses=_REFUSED,
    summary="Who this person was told what",
    description=(
        "Their in-app notices as the bell lists them, the push each was given "
        "as, and their emails from the outgoing mail queue, each linked to the "
        "local mail catcher once sent."
    ),
)
async def read_sent(
    account: SeedAccountDep,
    db: DbSession,
    settings: SettingsDep,
    notices: ReadRecentNoticesDep,
    pushes: NoticePushesDep,
    preferences: NotificationPreferencesRepositoryDep,
) -> SentResponse:
    recent = (await notices.execute(account.id, limit=MOST_RECENT)).notices
    pushed = await pushes.of([listed.notice for listed in recent])
    phones = await preferences.tokens_of(account.id)
    address = account.email.value
    queued = await db.execute(
        select(
            MailQueueORM.id,
            MailQueueORM.kind,
            MailQueueORM.subject,
            MailQueueORM.queued_at,
            MailQueueORM.sent_at,
            MailQueueORM.given_up_at,
            MailQueueORM.attempts,
            MailQueueORM.last_error,
        )
        .where(MailQueueORM.recipient == address)
        .order_by(MailQueueORM.queued_at.desc(), MailQueueORM.id)
        .limit(MOST_RECENT)
    )
    return SentResponse(
        email=address,
        phones=len(phones),
        notices=[
            SentNotice(
                listed=NoticeSchema.from_recent(listed),
                pushed=None
                if push is None
                else SentPush(title=push.title, body=push.body, data=dict(push.data)),
            )
            for listed, push in zip(recent, pushed, strict=True)
        ],
        emails=[
            SentEmail(
                mail_id=row.id,
                kind=row.kind,
                subject=row.subject,
                queued_at=stored_instant(row.queued_at),
                sent_at=stored_instant_or_none(row.sent_at),
                given_up_at=stored_instant_or_none(row.given_up_at),
                attempts=row.attempts,
                last_error=row.last_error,
                in_the_mail_catcher=(
                    in_the_mail_catcher(settings.MAIL_CATCHER_URL, row.id)
                    if row.sent_at is not None
                    else None
                ),
            )
            for row in queued
        ],
    )
