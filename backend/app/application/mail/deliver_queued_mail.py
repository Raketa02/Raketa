"""The mail worker's one run: send what is due, then forget what it said.

**One message per transaction** (``docs/adr/0186`` §2). A message is claimed
with ``FOR UPDATE SKIP LOCKED``, sent, marked and committed before the next is
claimed, so the claim is held for exactly one send. Claiming a batch and
committing after the first would release the rest to a second worker mid-batch,
and each of those would go twice.

**At least once.** A process that dies between the send and the commit sends
that message again on the next run. Each copy carries the same credential, so
either works and the second is only noise; a lost one is not harmless, which is
why the order is send-then-mark and never the reverse.

**The purge is the control** on a live secret sitting in the database, so it is
not optional on either path: a sent message loses its body, and so does one the
worker has given up on — a code does not outlive the attempt to deliver it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Final, final

from app.application.ports.mail import Mailer, MailerUnavailable, PendingMail
from app.application.ports.unit_of_work import UnitOfWork
from app.kernel import Clock, Instant, instant

#: How long a failed message waits before each retry, in order. **Five retries
#: over about fifty minutes**, then the worker gives up: the shortest credential
#: an email carries lives an hour (``docs/adr/0184`` §3), so an email still
#: undelivered after that would open nothing. Operational, not domain — a relay
#: that is down for a minute should cost a person a minute.
RETRY_AFTER: Final[tuple[timedelta, ...]] = (
    timedelta(seconds=15),
    timedelta(minutes=1),
    timedelta(minutes=5),
    timedelta(minutes=15),
    timedelta(minutes=30),
)


def retry_at(*, failed_attempts: int, now: Instant) -> Instant | None:
    """When a message that has now failed ``failed_attempts`` times is tried
    again, or ``None`` once the retries are spent."""

    if failed_attempts > len(RETRY_AFTER):
        return None
    return instant(now + RETRY_AFTER[failed_attempts - 1])


@final
@dataclass(frozen=True, slots=True)
class MailRun:
    """What one run did, for the log line."""

    sent: int
    failed: int
    given_up: int


class DeliverQueuedMail:
    """Send up to ``batch_size`` due messages through ``mailer``."""

    def __init__(
        self,
        *,
        pending: PendingMail,
        mailer: Mailer,
        uow: UnitOfWork,
        clock: Clock,
        batch_size: int,
    ) -> None:
        self._pending = pending
        self._mailer = mailer
        self._uow = uow
        self._clock = clock
        self._batch_size = batch_size

    async def execute(self) -> MailRun:
        sent = failed = given_up = 0
        for _ in range(self._batch_size):
            queued = await self._pending.next_due(now=self._clock.now())
            if queued is None:
                break
            try:
                await self._mailer.send(queued.message, mail_id=queued.id)
            except MailerUnavailable as exc:
                attempts = queued.attempts + 1
                now = self._clock.now()
                again = retry_at(failed_attempts=attempts, now=now)
                await self._pending.mark_failed(
                    queued.id,
                    attempts=attempts,
                    # The mailer's own account of the refusal — the relay's code,
                    # host or timeout. A mailer never puts the body in one.
                    error=str(exc)[:500],
                    retry_at=again,
                    at=now,
                )
                await self._uow.commit()
                failed += 1
                if again is None:
                    given_up += 1
                continue
            await self._pending.mark_sent(queued.id, at=self._clock.now())
            await self._uow.commit()
            sent += 1
        return MailRun(sent=sent, failed=failed, given_up=given_up)
