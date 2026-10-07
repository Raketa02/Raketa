"""The mailer, speaking SMTP (``docs/adr/0186`` §1).

**One adapter for every environment.** Locally it points at the mail catcher in
the dev stack, whose web inbox is ``localhost:8025`` and from which nothing
leaves the machine; deployed, it points at a real relay — the same class with a
different host, as the photo store is the same class against MinIO and S3. The
production relay stays unconfigured until a domain exists, and a deployed
environment without one refuses to start (``app/core/config.py``).

**Standard library only.** ``smtplib`` is blocking, so a send runs in a worker
thread and never on the event loop; the worker sends one message at a time, so
there is never more than one thread per process doing this. Adding an async SMTP
client would be a dependency bought for a loop that sends a handful of emails.
"""

from __future__ import annotations

import asyncio
import smtplib
import socket
import ssl
from collections.abc import Callable
from email.message import EmailMessage
from email.utils import formatdate
from typing import Optional
from uuid import UUID

from app.application.ports.mail import MailerUnavailable, OutgoingMessage
from app.core.config import SmtpSecurity


def compose(message: OutgoingMessage, *, sender: str, mail_id: UUID) -> EmailMessage:
    """The message as a mailbox receives it: plain text, with the HTML as its
    alternative, so a mail program that shows no HTML still shows every word.

    **Its Message-ID is its queue row's id** at the sender's domain — unique,
    since no two rows share one, and the same on every attempt, so a copy the
    worker sent twice (it sends at least once) is one message to a mailbox.
    The dev console searches the mail catcher for it (#594)."""

    email = EmailMessage()
    email["From"] = sender
    email["To"] = message.to
    email["Subject"] = message.subject
    email["Date"] = formatdate(localtime=False)
    email["Message-ID"] = f"<{mail_id}@{_domain_of(sender) or socket.getfqdn()}>"
    email.set_content(message.text)
    email.add_alternative(message.html, subtype="html")
    return email


def _domain_of(sender: str) -> Optional[str]:
    address = sender.rsplit("<", 1)[-1].rstrip(">").strip()
    return address.rsplit("@", 1)[1] if "@" in address else None


def _connect_over_tls(host: str, port: int, *, timeout: float) -> smtplib.SMTP:
    # With the default context, which verifies the relay's certificate and its
    # name. ``SMTP_SSL`` without one uses the standard library's unverified
    # context, and a relay nobody checked is a relay anybody can be.
    return smtplib.SMTP_SSL(
        host, port, timeout=timeout, context=ssl.create_default_context()
    )


class SmtpMailer:
    """``Mailer`` over an SMTP relay."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        security: SmtpSecurity,
        username: Optional[str],
        password: Optional[str],
        sender: str,
        timeout_seconds: float,
        connect: Optional[Callable[..., smtplib.SMTP]] = None,
    ) -> None:
        self._host = host
        self._port = port
        self._security = security
        self._username = username
        self._password = password
        self._sender = sender
        self._timeout = timeout_seconds
        self._connect = connect or (
            _connect_over_tls if security is SmtpSecurity.TLS else smtplib.SMTP
        )

    async def send(self, message: OutgoingMessage, *, mail_id: UUID) -> None:
        email = compose(message, sender=self._sender, mail_id=mail_id)
        try:
            await asyncio.to_thread(self._send, email)
        except (smtplib.SMTPException, OSError) as exc:
            # The exception names the relay's refusal — a code, a host, a
            # timeout. It never carries the body, which is what the worker writes
            # to the queue's error column.
            raise MailerUnavailable(f"{type(exc).__name__}: {exc}") from exc

    def _send(self, email: EmailMessage) -> None:
        with self._connect(self._host, self._port, timeout=self._timeout) as smtp:
            if self._security is SmtpSecurity.STARTTLS:
                smtp.starttls(context=ssl.create_default_context())
            if self._username:
                smtp.login(self._username, self._password or "")
            smtp.send_message(email)
