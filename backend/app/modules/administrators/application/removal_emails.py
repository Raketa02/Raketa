"""The two emails a removal sends, as a person reads them (``docs/adr/0191``
§4–§5).

The app hears a removal only on its next administrator request, and only while
it is open (``docs/adr/0184`` §7), so somebody away from it would find out by
their groups vanishing. **The email is what tells them, and it is a notice**:
it asks nothing and opens nothing, so it carries no button and no code.

- **Somebody who ran the club's groups** — they took up the invitation, and
  the club may since have reset their password — is told they were removed,
  and that their account and anything they do on it as a player stay.
- **Somebody still invited** is told the invitation is withdrawn, because its
  link would otherwise read *expired — ask the club to send a new one*, and
  the club is who withdrew it.

The words are the backend's (``docs/adr/0186`` §4), signed *Raketa*.
"""

from __future__ import annotations

from typing import Final

from app.application.mail.layout import ButtonEmail, render
from app.application.ports.mail import OutgoingMessage

#: The ``kind`` each message is queued under — what outlives the purge.
REMOVED_KIND: Final = "administrator_removal.removed"
WITHDRAWN_KIND: Final = "administrator_removal.invitation_withdrawn"


def removed_email(*, to: str, name: str, club_name: str) -> OutgoingMessage:
    return render(
        ButtonEmail(
            kind=REMOVED_KIND,
            to=to,
            subject=f"{club_name} removed you as an administrator",
            heading=f"Hi {name}, {club_name} removed you as an administrator",
            lines=(
                f"You no longer run {club_name}'s groups on Raketa, and they no "
                f"longer show in the app. The groups stay with {club_name}.",
                "Your Raketa account stays, and so does anything you do on it as "
                "a player.",
            ),
            footer=f"If this is a surprise, ask {club_name} about it.",
        )
    )


def withdrawn_email(*, to: str, name: str, club_name: str) -> OutgoingMessage:
    return render(
        ButtonEmail(
            kind=WITHDRAWN_KIND,
            to=to,
            subject=f"{club_name} withdrew its invitation",
            heading=f"Hi {name}, {club_name} withdrew its invitation",
            lines=(
                f"{club_name} no longer wants you to run its groups on Raketa as "
                f"an administrator.",
                "The invitation it sent you no longer works.",
            ),
            footer=f"If this is a surprise, ask {club_name} about it.",
        )
    )
