"""A mailer that keeps what it was given, for tests that read the emails sent.

The adapter the API suite replaces the SMTP mailer with (``docs/adr/0186`` §5):
**no test in this suite needs a mail catcher running**, as none needs MinIO or
Redis. It can also be told to refuse, which is how the worker's retry and give-up
paths are driven without a relay to take down.
"""

from __future__ import annotations

from app.application.ports.mail import MailerUnavailable, OutgoingMessage


class RecordingMailer:
    def __init__(self) -> None:
        self.sent: list[OutgoingMessage] = []
        self._refusals = 0

    def refuse_next(self, times: int = 1) -> None:
        """The next ``times`` sends fail as a relay that is down fails."""

        self._refusals += times

    async def send(self, message: OutgoingMessage) -> None:
        if self._refusals:
            self._refusals -= 1
            raise MailerUnavailable("the relay is down (test)")
        self.sent.append(message)

    def to(self, address: str) -> list[OutgoingMessage]:
        return [message for message in self.sent if message.to == address]
