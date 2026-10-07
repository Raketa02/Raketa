"""The mail worker: send what is due, retry what failed, and forget both.

``docs/adr/0186`` §2, driven through the production worker over the real queue
table: a message sent loses its body, a message the relay refused waits and is
tried again, and a message the worker gives up on loses its body too — a code
never outlives the attempt to deliver it.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.application.mail.deliver_queued_mail import (
    RETRY_AFTER,
    DeliverQueuedMail,
    retry_at,
)
from app.application.ports.mail import OutgoingMessage
from app.bootstrap.composition import (
    build_mail_queue,
    build_pending_mail,
    build_unit_of_work,
)
from app.infrastructure.mail.mail_queue_model import MailQueueORM
from app.kernel import instant
from tests.unit.fake_clock import MovableClock
from tests.unit.fake_mailer import RecordingMailer

SECRET = "K7M4QX2P"


def a_message(to: str = "tomek@example.com") -> OutgoingMessage:
    return OutgoingMessage(
        kind="forgot_password.player",
        to=to,
        subject="Set a new Raketa password",
        text=f"Your code:\n\n{SECRET}\n",
        html=f"<p>{SECRET}</p>",
    )


@pytest.fixture
def clock() -> MovableClock:
    return MovableClock(datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc))


@pytest.fixture
def mailer() -> RecordingMailer:
    return RecordingMailer()


async def queue(session_factory, clock, *messages: OutgoingMessage) -> None:
    async with session_factory() as session:
        for message in messages:
            await build_mail_queue(session).enqueue(message, at=clock.now())
        await session.commit()


async def run(session_factory, mailer, clock, *, batch_size: int = 20):
    async with session_factory() as session:
        return await DeliverQueuedMail(
            pending=build_pending_mail(session),
            mailer=mailer,
            uow=build_unit_of_work(session),
            clock=clock,
            batch_size=batch_size,
        ).execute()


async def the_row(session_factory) -> MailQueueORM:
    async with session_factory() as session:
        return (await session.execute(select(MailQueueORM))).scalar_one()


async def test_a_queued_message_is_sent_once_and_its_body_purged(
    session_factory, mailer, clock
):
    await queue(session_factory, clock, a_message())

    first = await run(session_factory, mailer, clock)
    second = await run(session_factory, mailer, clock)

    assert (first.sent, second.sent) == (1, 0)
    assert mailer.sent == [a_message()]
    row = await the_row(session_factory)
    assert row.sent_at is not None
    assert row.text_body is None and row.html_body is None
    assert SECRET not in repr(row.__dict__)


async def test_messages_go_oldest_first_and_a_batch_is_a_bound(
    session_factory, mailer, clock
):
    await queue(session_factory, clock, a_message("first@example.com"))
    clock.move(timedelta(seconds=1))
    await queue(session_factory, clock, a_message("second@example.com"))

    run_one = await run(session_factory, mailer, clock, batch_size=1)

    assert run_one.sent == 1
    assert [m.to for m in mailer.sent] == ["first@example.com"]
    await run(session_factory, mailer, clock)
    assert [m.to for m in mailer.sent] == ["first@example.com", "second@example.com"]


async def test_a_refused_message_waits_and_is_tried_again(
    session_factory, mailer, clock
):
    await queue(session_factory, clock, a_message())
    mailer.refuse_next()

    refused = await run(session_factory, mailer, clock)
    too_soon = await run(session_factory, mailer, clock)
    clock.move(RETRY_AFTER[0])
    retried = await run(session_factory, mailer, clock)

    assert (refused.failed, too_soon.sent, retried.sent) == (1, 0, 1)
    assert mailer.sent == [a_message()]
    row = await the_row(session_factory)
    assert row.attempts == 1
    assert "relay is down" in row.last_error
    assert row.text_body is None


async def test_every_attempt_at_one_email_is_sent_under_its_queue_id(
    session_factory, mailer, clock
):
    """The id is the email's Message-ID, so a retried copy is the same message
    to a mailbox — and the dev console finds it in the mail catcher by it."""

    await queue(session_factory, clock, a_message())
    mailer.refuse_next()

    await run(session_factory, mailer, clock)
    clock.move(RETRY_AFTER[0])
    await run(session_factory, mailer, clock)

    row = await the_row(session_factory)
    assert mailer.tried == [row.id, row.id]
    assert list(mailer.sent_under) == [row.id]


async def test_the_worker_gives_up_and_forgets_the_body_all_the_same(
    session_factory, mailer, clock
):
    await queue(session_factory, clock, a_message())
    mailer.refuse_next(len(RETRY_AFTER) + 1)

    for wait in (timedelta(0), *RETRY_AFTER):
        clock.move(wait)
        await run(session_factory, mailer, clock)
    clock.move(timedelta(days=1))
    after = await run(session_factory, mailer, clock)

    assert mailer.sent == []
    assert after.sent == after.failed == 0
    row = await the_row(session_factory)
    assert row.given_up_at is not None
    assert row.attempts == len(RETRY_AFTER) + 1
    assert row.text_body is None and row.html_body is None


def test_the_retries_are_spent_within_the_shortest_credential_s_hour() -> None:
    """An email still undelivered after an hour would open nothing: a forgotten
    password's credential lives one (``docs/adr/0184`` §3)."""

    assert sum(RETRY_AFTER, timedelta()) < timedelta(hours=1)
    now = instant(datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc))
    assert retry_at(failed_attempts=1, now=now) == now + RETRY_AFTER[0]
    assert retry_at(failed_attempts=len(RETRY_AFTER) + 1, now=now) is None
