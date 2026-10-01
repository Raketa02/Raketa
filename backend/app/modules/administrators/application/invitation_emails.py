"""The invitation emails, as a person reads them (``docs/adr/0186`` §3).

Three messages, one per way in:

- **a new person** gets a button to the public site's ``/invite/<token>`` and
  the code under it — the page sets a password, and the code does the same
  from the app's *Have an invitation code?*;
- **an existing account** gets *"[Club] wants to make you an administrator"*
  and a button that opens the app, and **no code**: no credential and no
  password is involved;
- **the club's reset of an administrator** gets the invitation's own page and
  a code, because it puts the person back to *invited* and that page already
  sets a password for exactly that state.

A resend is the same message again. The words are the backend's
(``docs/adr/0186`` §4); every one is signed *Raketa*.
"""

from __future__ import annotations

from typing import Final

from app.application.mail.layout import ButtonEmail, OnScreen, render
from app.application.ports.mail import OutgoingMessage

#: The ``kind`` each message is queued under — what outlives the purge.
NEW_PERSON_KIND: Final = "administrator_invitation.new_person"
EXISTING_ACCOUNT_KIND: Final = "administrator_invitation.existing_account"
CLUB_RESET_KIND: Final = "administrator_invitation.club_reset"

#: The two labels are the sign-in screen's own, and what the person looks for.
_CODE_LINE: Final = (
    "Or open the Raketa app, tap ",
    OnScreen("Have an invitation code?"),
    " under ",
    OnScreen("Sign in"),
    ", and enter this code:",
)


def new_person_email(
    *, to: str, name: str, club_name: str, link: str, code: str
) -> OutgoingMessage:
    return render(
        ButtonEmail(
            kind=NEW_PERSON_KIND,
            to=to,
            subject=f"{club_name} invited you to run its groups on Raketa",
            heading=f"Hi {name}, {club_name} invited you to Raketa",
            lines=(
                f"{club_name} wants you to run its groups on Raketa as an "
                f"administrator. Set a password to get started.",
                "The button and the code below work for 72 hours, and each works once.",
            ),
            button_label="Set your password",
            button_url=link,
            code=code,
            code_line=_CODE_LINE,
            footer=(
                "If you weren't expecting this, you can ignore this email. "
                "Nothing happens until a password is set."
            ),
        )
    )


def existing_account_email(
    *, to: str, club_name: str, app_link: str
) -> OutgoingMessage:
    return render(
        ButtonEmail(
            kind=EXISTING_ACCOUNT_KIND,
            to=to,
            subject=f"{club_name} wants to make you an administrator",
            heading=f"{club_name} wants to make you an administrator",
            lines=(
                f"{club_name} wants you to run its groups on Raketa. "
                f"Open Raketa, signed in as {to}, and accept the invitation "
                f"there.",
                "No new password is needed: it is added to the account you "
                "already have. The invitation is open for 72 hours.",
            ),
            button_label="Open Raketa",
            button_url=app_link,
            footer=(
                "If you weren't expecting this, you can ignore this email. "
                "Nothing changes unless you accept."
            ),
        )
    )


def club_reset_email(
    *, to: str, name: str, club_name: str, link: str, code: str
) -> OutgoingMessage:
    return render(
        ButtonEmail(
            kind=CLUB_RESET_KIND,
            to=to,
            subject=f"{club_name} reset your Raketa password",
            heading=f"Hi {name}, set a new password",
            lines=(
                f"{club_name} reset the password of your Raketa administrator "
                f"account and signed it out everywhere.",
                "Set a new one with the button or the code below within 72 "
                "hours. Each works once.",
            ),
            button_label="Set a new password",
            button_url=link,
            code=code,
            code_line=_CODE_LINE,
            footer=(
                f"If this is a surprise, ask {club_name} about it. Until a new "
                f"password is set, nobody can sign in to this account."
            ),
        )
    )
