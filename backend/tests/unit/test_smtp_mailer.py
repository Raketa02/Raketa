"""The SMTP adapter: what it hands a relay, and how it fails.

``docs/adr/0186`` §1. The relay is a stand-in connection recording what it was
asked to do, so no test here needs a mail catcher running; the dev stack's
Mailpit is where the real thing is looked at by hand.
"""

from __future__ import annotations

import smtplib

import pytest

from app.application.ports.mail import MailerUnavailable, OutgoingMessage
from app.core.config import SmtpSecurity
from app.infrastructure.mail.smtp_mailer import SmtpMailer, compose

SENDER = "Raketa <no-reply@raketa.example>"
MESSAGE = OutgoingMessage(
    kind="forgot_password.player",
    to="tomek@example.com",
    subject="Set a new Raketa password",
    text="Set a new password:\nhttps://raketa.example/reset/abc\n\nK7M4QX2P\n",
    html='<p><a href="https://raketa.example/reset/abc">Set</a></p><p>K7M4QX2P</p>',
)


class StandInRelay:
    """Records one connection's conversation, or refuses it."""

    conversations: list["StandInRelay"] = []

    def __init__(self, host, port, *, timeout, refuse=None) -> None:
        self.address = (host, port, timeout)
        self.steps: list[str] = []
        self.sent = []
        self._refuse = refuse
        StandInRelay.conversations.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.steps.append("quit")

    def starttls(self, *, context) -> None:
        self.steps.append("starttls")

    def login(self, username, password) -> None:
        self.steps.append(f"login {username}")

    def send_message(self, email) -> None:
        if self._refuse is not None:
            raise self._refuse
        self.steps.append("send")
        self.sent.append(email)


@pytest.fixture(autouse=True)
def fresh_conversations():
    StandInRelay.conversations = []


def mailer(**overrides) -> SmtpMailer:
    options = dict(
        host="mailpit",
        port=1025,
        security=SmtpSecurity.NONE,
        username=None,
        password=None,
        sender=SENDER,
        timeout_seconds=10.0,
        connect=StandInRelay,
    )
    options.update(overrides)
    return SmtpMailer(**options)


def test_a_message_is_plain_text_with_the_html_as_its_alternative() -> None:
    email = compose(MESSAGE, sender=SENDER)

    assert email["From"] == SENDER
    assert email["To"] == "tomek@example.com"
    assert email["Subject"] == "Set a new Raketa password"
    assert email["Message-ID"].endswith("@raketa.example>")
    assert email.get_content_type() == "multipart/alternative"
    text, html = email.iter_parts()
    assert text.get_content_type() == "text/plain"
    assert "K7M4QX2P" in text.get_content()
    assert html.get_content_type() == "text/html"
    assert 'href="https://raketa.example/reset/abc"' in html.get_content()


async def test_the_local_catcher_is_spoken_to_in_the_clear_and_anonymously() -> None:
    await mailer().send(MESSAGE)

    (relay,) = StandInRelay.conversations
    assert relay.address == ("mailpit", 1025, 10.0)
    assert relay.steps == ["send", "quit"]
    assert relay.sent[0]["To"] == "tomek@example.com"


async def test_a_relay_is_upgraded_to_tls_before_anybody_signs_in() -> None:
    await mailer(
        security=SmtpSecurity.STARTTLS, username="raketa", password="relay-pwd"
    ).send(MESSAGE)

    (relay,) = StandInRelay.conversations
    assert relay.steps == ["starttls", "login raketa", "send", "quit"]


@pytest.mark.parametrize(
    "refusal",
    [
        smtplib.SMTPRecipientsRefused({"tomek@example.com": (550, b"no")}),
        smtplib.SMTPServerDisconnected("gone"),
        ConnectionRefusedError("nobody is listening"),
    ],
)
async def test_a_relay_that_cannot_take_it_is_unavailable(refusal) -> None:
    def refusing(host, port, *, timeout):
        return StandInRelay(host, port, timeout=timeout, refuse=refusal)

    with pytest.raises(MailerUnavailable) as raised:
        await mailer(connect=refusing).send(MESSAGE)

    # The worker writes this message to the queue's error column, so it names
    # the refusal and never carries the body.
    assert "K7M4QX2P" not in str(raised.value)
