"""The *Forgot password?* email, as a person reads it (``docs/adr/0186`` §3).

One message, worded for the account it recovers: a player's or an
administrator's in the app, or a club's on its website. Each carries a button to
the page that sets a new password and the code that does the same from wherever
the person asked.
"""

from __future__ import annotations

from typing import Final

from app.application.mail.layout import ButtonEmail, render
from app.application.ports.mail import OutgoingMessage
from app.modules.auth.domain.audience import Audience

#: The ``kind`` each audience's reset is queued under — what outlives the purge.
RESET_EMAIL_KINDS: Final = {
    Audience.PLAYER_APP: "forgot_password.player",
    Audience.CLUB: "forgot_password.club",
}

_WHERE_THE_CODE_GOES: Final = {
    Audience.PLAYER_APP: "in the Raketa app",
    Audience.CLUB: "on the Raketa for Clubs sign-in page",
}


def reset_email(
    *, audience: Audience, to: str, link: str, code: str
) -> OutgoingMessage:
    return render(
        ButtonEmail(
            kind=RESET_EMAIL_KINDS[audience],
            to=to,
            subject="Set a new Raketa password",
            heading="Set a new password",
            lines=(
                f"Somebody asked to set a new password for {to}. If it was you, "
                f"use the button or the code below within the next hour. Each "
                f"works once.",
            ),
            button_label="Set a new password",
            button_url=link,
            code=code,
            code_line=f"Or enter this code {_WHERE_THE_CODE_GOES[audience]}:",
            footer=(
                "If it wasn't you, you can ignore this email. Your password "
                "stays as it is."
            ),
        )
    )
