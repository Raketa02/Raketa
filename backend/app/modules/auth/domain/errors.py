"""Authentication errors, each with its own wire code.

Every one of these is a 401, and the status alone therefore says almost nothing.
The codes are what let a client tell "rotate the token and retry" from "this
session is over" from "this account is disabled" — the distinction the 401 →
refresh → retry rotation is built on — without reading a message that will be
reworded and localized.
"""

from app.shared.domain import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    UnauthorizedError,
)


class InvalidCredentials(UnauthorizedError):
    code = "invalid_credentials"

    def __init__(self) -> None:
        # Identical message on email-not-found vs wrong-password — no enumeration.
        # The code is identical for the same reason.
        super().__init__("invalid email or password")


class AccountDisabled(UnauthorizedError):
    code = "account_disabled"

    def __init__(self) -> None:
        super().__init__("account disabled")


class InvalidRefreshToken(UnauthorizedError):
    code = "invalid_refresh_token"

    def __init__(self, message: str = "invalid refresh token") -> None:
        super().__init__(message)


class RefreshTokenExpired(UnauthorizedError):
    code = "refresh_token_expired"

    def __init__(self) -> None:
        super().__init__("refresh token expired")


class RefreshTokenRevoked(UnauthorizedError):
    code = "refresh_token_revoked"

    def __init__(self) -> None:
        super().__init__("refresh token has been revoked")


class RefreshTokenNotRecognised(UnauthorizedError):
    code = "refresh_token_not_recognised"

    def __init__(self) -> None:
        super().__init__("refresh token not recognised")


class RefreshTokenMismatch(UnauthorizedError):
    code = "refresh_token_mismatch"

    def __init__(self) -> None:
        super().__init__("refresh token does not match")


# --- The access token, as the request boundary sees it -------------------------
#
# These were raised as the bare base class, so the only thing separating "you
# sent no token" from "your token expired" was the message — exactly the branch
# the contract forbids. A client refreshing on expiry and prompting a sign-in on
# absence needs them apart.


class AccessTokenMissing(UnauthorizedError):
    code = "access_token_missing"

    def __init__(self) -> None:
        super().__init__("missing bearer token")


class AccessTokenExpired(UnauthorizedError):
    code = "access_token_expired"

    def __init__(self) -> None:
        super().__init__("access token expired")


class AccessTokenInvalid(UnauthorizedError):
    code = "access_token_invalid"

    def __init__(self) -> None:
        super().__init__("invalid access token")


class AccessTokenSubjectMalformed(UnauthorizedError):
    code = "access_token_subject_malformed"

    def __init__(self) -> None:
        super().__init__("malformed token subject")


class AccessTokenRevoked(UnauthorizedError):
    """The token was issued before its account's credentials changed.

    **Signing out everywhere** (``docs/adr/0185`` §7): a password set through
    *Forgot password?* moves the account's credentials-changed instant, and
    every access token issued before it is refused from the next request on —
    as its refresh tokens already are. The client meets this as any other 401:
    it refreshes, the refresh is refused as revoked, and the session ends.
    """

    code = "access_token_revoked"

    def __init__(self) -> None:
        super().__init__("signed out: this account's password has changed")


# --- One-time credentials (docs/adr/0184 §3) -----------------------------------
#
# Four refusals a person is shown, each with its own sentence on the client —
# *wrong code*, *expired* (ask again), *used* and *locked* — plus the one a
# tampered link or a stale ticket meets. **A claim by email and code only ever
# says which of the last three it is to somebody who typed the right code**:
# said to anybody else, *locked* or *expired* would tell them the email has an
# account, which is what the request's identical answer exists to hide.


class CredentialCodeIncorrect(BadRequestError):
    """The code is not the one sent to that email — or nothing was sent to it."""

    code = "code_incorrect"

    def __init__(self) -> None:
        super().__init__(
            "that code is not the one we sent to that email",
            details={"field": "code"},
        )


class CredentialNotFound(NotFoundError):
    """A link or a ticket this backend never issued."""

    code = "credential_not_found"

    def __init__(self) -> None:
        super().__init__("that link is not one we sent")


class CredentialExpired(ConflictError):
    code = "credential_expired"

    def __init__(self) -> None:
        super().__init__("that link and code have expired")


class CredentialUsed(ConflictError):
    code = "credential_used"

    def __init__(self) -> None:
        super().__init__("that link and code have already been used")


class CredentialLocked(ConflictError):
    code = "credential_locked"

    def __init__(self) -> None:
        super().__init__("too many wrong codes: that link and code are locked")


class TicketExpired(ConflictError):
    """The code was right, and then too long passed before the password came.
    The code still works: typing it again is a fresh ticket."""

    code = "ticket_expired"

    def __init__(self) -> None:
        super().__init__("that took too long: enter the code again")
