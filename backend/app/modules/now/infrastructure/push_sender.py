"""Where a composed message goes until a transport is provisioned.

**The transport is the one thing in this channel that cannot be built here.**
Everything ADR-0062 and ADR-0065 decide — the past-tense wording, the collapse
id, the interruption level, the one Android channel — is expressible through
Expo's push API and through bare APNs/FCM alike (`Raketa02/Raketa#25`), and the
choice between them has never had to be made. What has to exist before either
can be called is a Firebase project, an Expo project id and an Apple Developer
Program membership, which are `Raketa02/Raketa#26` and
`Raketa02/Raketa#37` and are a **human's** work: an agent may not create a
credential file (`CLAUDE.md`).

So this adapter **is** the port's only implementation today, and it is honest
about what it is rather than being an HTTP client written against a service
nobody can reach. It draws the line where the OS would draw it: in `local`, the
log is the lock screen.

**It withdraws nothing and can withdraw nothing**, which is not a limitation of
this implementation but the whole design (ADR-0062): no platform offers
server-side removal of a delivered alert as a guarantee, so the retraction is
carried by the wording and there is no operation here to be missing.
"""

from __future__ import annotations

import logging
from typing import Sequence

from app.modules.now.domain.push import PushMessage

logger = logging.getLogger(__name__)

#: How much of a token is printed. A push token is an **address that is also a
#: capability** — anybody holding it and a provider key can write to that
#: phone — so a log line carrying whole tokens is a log line that must be
#: guarded like a credential store. The tail is enough to tell two phones apart
#: while reading a local run, which is the only thing this is for.
TOKEN_TAIL = 6


class LoggingPushSender:
    """The sink that stands in for APNs and FCM until either is provisioned."""

    async def send(self, messages: Sequence[PushMessage]) -> None:
        """Draw each message where a developer can read it.

        One line per message rather than one per batch, because the unit that
        matters is *what one phone was shown*: a batch line would hide the fact
        that a player with two phones is sent the same body twice under one
        collapse id, which is exactly the behaviour somebody reading this log is
        checking.
        """

        for message in messages:
            logger.info(
                "push message composed",
                extra={
                    "platform": message.platform.value,
                    "token": f"…{message.token[-TOKEN_TAIL:]}",
                    "collapse_id": message.collapse_id,
                    "interruption_level": (
                        None
                        if message.interruption_level is None
                        else message.interruption_level.value
                    ),
                    "channel_id": message.channel_id,
                    "body": message.body,
                },
            )
