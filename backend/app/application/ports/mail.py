"""Email: the queue a use case writes to, and the mailer a worker sends through.

**A use case never sends** (``docs/adr/0186`` §2). It renders the whole message —
recipient, subject, plain text and HTML, link and code included — and hands it
to :class:`MailQueue`, which writes it **in the caller's transaction**: the
email and the act that caused it commit together or not at all, so an
invitation cannot leave for an administrator a rollback un-made.

**A worker sends**, through :class:`Mailer`, and then purges the body
(:class:`PendingMail`). The queue row is the one place a secret sits, for as long
as it takes to send it; what outlives the send is what a person debugging
delivery needs — the kind, the recipient, the subject, when it went and whether
it failed.

**This is a second queue, not the outbox** (``docs/adr/0003``, narrowed). The
outbox carries domain events, and a domain event may never carry a secret
(``docs/adr/0184`` §4).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant


@final
@dataclass(frozen=True, slots=True)
class OutgoingMessage:
    """One rendered email, ready for a mailbox.

    ``kind`` says which message it is — ``forgot_password.player`` — and is the
    one field that names the message rather than carrying it: it survives the
    purge, so a person debugging delivery can still say *which* email failed.
    """

    kind: str
    to: str
    subject: str
    text: str
    html: str


@final
@dataclass(frozen=True, slots=True)
class QueuedMail:
    """A message waiting in the queue, and how many times sending it has failed."""

    id: UUID
    message: OutgoingMessage
    attempts: int


@runtime_checkable
class MailQueue(Protocol):
    """Where a use case leaves an email for the worker."""

    async def enqueue(self, message: OutgoingMessage, *, at: Instant) -> None:
        """Write ``message`` to the queue in the caller's transaction, without
        committing it. ``at`` is when it was queued."""
        ...


@runtime_checkable
class PendingMail(Protocol):
    """The worker's side of the queue."""

    async def next_due(self, *, now: Instant) -> Optional[QueuedMail]:
        """The oldest message due a send, **claimed** so that a second worker
        beside this one skips it (``FOR UPDATE SKIP LOCKED``), or ``None``. The
        claim lasts until the caller's transaction ends."""
        ...

    async def mark_sent(self, mail_id: UUID, *, at: Instant) -> None:
        """Record the send and **purge the body** — the text and the HTML, which
        is where a link and a code live. Not committed."""
        ...

    async def mark_failed(
        self,
        mail_id: UUID,
        *,
        attempts: int,
        error: str,
        retry_at: Optional[Instant],
        at: Instant,
    ) -> None:
        """Record a failed send. With ``retry_at`` the message waits until then;
        without it the worker has **given up**, and the body is purged exactly as
        a sent one's is — a secret does not outlive the attempt to deliver it.
        Not committed."""
        ...


class MailerUnavailable(Exception):
    """The mailer could not send one message. The worker tries again later."""


@runtime_checkable
class Mailer(Protocol):
    """Sends one rendered message. Raises :class:`MailerUnavailable` when it
    cannot, and never decides whether to retry."""

    async def send(self, message: OutgoingMessage) -> None: ...
