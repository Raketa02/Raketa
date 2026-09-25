"""What *Forgot password?*'s three routes say about themselves, on both surfaces.

The player app's and the club website's routes are the same three acts built
for two audiences, so their documentation is written once here and each router
names only what differs: where the link opens, and what *signed in elsewhere*
means on that surface.
"""

from __future__ import annotations

from typing import Any, Final

from fastapi import status

from app.core.exception_handlers import ErrorResponse

REQUEST_RESPONSES: Final[dict[int | str, dict[str, Any]]] = {
    status.HTTP_202_ACCEPTED: {
        "description": (
            "Accepted — **the same answer whether or not the address has an "
            "account**, and whether or not an email was sent."
        ),
    },
}

CLAIM_RESPONSES: Final[dict[int | str, dict[str, Any]]] = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": (
            "`code_incorrect` (`details.field`: `code`) — not the code sent to "
            "that address, **or nothing was sent to it**: the two are one "
            "answer. Five wrong codes lock the credential."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "The code is right, and it can no longer be used: "
            "`credential_expired` (ask again), `credential_used` or "
            "`credential_locked` (five wrong codes)."
        ),
    },
}

NEW_PASSWORD_RESPONSES: Final[dict[int | str, dict[str, Any]]] = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": (
            "`password_too_weak` (`details.field`: `password`) — 8 to 128 "
            "characters with a letter and a digit. The link and the code still "
            "work."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`credential_not_found` — a link or a ticket this surface never issued."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "`credential_expired` (ask again), `credential_used`, "
            "`credential_locked`, or `ticket_expired` — the code was right and "
            "the password came too late; claiming the code again is a fresh "
            "ticket."
        ),
    },
}


def request_description(where_the_link_opens: str) -> str:
    return (
        "Sends an email with a button and an 8-character code, valid for "
        f"**one hour** and usable once. The button opens {where_the_link_opens}; "
        "the code does the same from wherever the person asked.\n\n"
        "**Nobody can use this to learn who has an account**: the answer is "
        "`202` with no body for an address with an account, without one, and for "
        "one asked for too often. **Throttled per address** — past three emails "
        "in an hour, a request sends nothing and says so to nobody. A newer "
        "email replaces the older one's link and code."
    )


def claim_description() -> str:
    return (
        "The address and the code from the email, exchanged for a short-lived "
        "`ticket` the new password is then set with. A claim is not a use: until "
        "a password is set, the same code can be claimed again.\n\n"
        "Only a **right** code learns why it cannot be used; a wrong one is "
        "`code_incorrect` whatever else is true."
    )


def new_password_description(elsewhere: str) -> str:
    return (
        "Sets the new password with **exactly one** of the email's link `token` "
        "or a claimed code's `ticket`, then **signs out everywhere** and signs "
        "this session in: every access token issued before this moment is "
        f"refused (`access_token_revoked`) and every refresh token revoked, so "
        f"another {elsewhere} still signed in is signed out on its next request. "
        "The answer is this session's new token pair. The link, the code and "
        "the ticket are spent."
    )
