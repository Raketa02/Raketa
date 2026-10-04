"""What an invitation's refusals say about themselves, on both surfaces that
set its password.

The app's *Set your password* and the public site's invitation page run one set
of rules (``application/invitations.py``), so the refusals they can meet are
written once here and each router names only what differs.
"""

from __future__ import annotations

from typing import Any, Final

from fastapi import status

from app.core.exception_handlers import ErrorResponse

CREDENTIAL_REFUSALS: Final[dict[int | str, dict[str, Any]]] = {
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "The invitation can no longer be used: `credential_expired` (ask the "
            "club to send a new one), `credential_used`, `credential_locked` "
            "(five wrong codes) — or `sign_in_to_accept`: the email has an "
            "account now, which accepts from the app, signed in."
        ),
    },
}

WEAK_PASSWORD: Final[dict[int | str, dict[str, Any]]] = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": (
            "`password_too_weak` (`details.field`: `password`) — 8 to 128 "
            "characters with a letter and a digit. The link and the code "
            "still work."
        ),
    },
}
