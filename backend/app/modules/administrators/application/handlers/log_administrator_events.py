"""The Administrators context's subscriber: a log line per event, and nothing
else.

Nothing reacts to an Administrator — the projection is written in the act's own
transaction, and the email in the mail queue beside it — but a delivered event
with no handler is a delivery failure, so each is logged as the clubs' are.
**The line carries neither the email nor the name**: the ids say which
administratorship it was.
"""

from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.modules.administrators.domain.events import (
    AdministratorInvited,
    AdministratorPasswordReset,
    AdministratorRemoved,
    InvitationAccepted,
    InvitationResent,
)

logger = logging.getLogger(__name__)

_LINES = {
    AdministratorInvited: "administrators.administrator.invited",
    InvitationResent: "administrators.invitation.resent",
    InvitationAccepted: "administrators.invitation.accepted",
    AdministratorPasswordReset: "administrators.administrator.password_reset",
    AdministratorRemoved: "administrators.administrator.removed",
}


class LogAdministratorEvent:
    async def __call__(
        self,
        event: AdministratorInvited
        | InvitationResent
        | InvitationAccepted
        | AdministratorPasswordReset
        | AdministratorRemoved,
        context: DeliveryContext,
    ) -> None:
        logger.info(
            _LINES[type(event)],
            extra={
                "administrator_id": str(event.administrator_id),
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )
