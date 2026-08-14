"""Authentication errors, each with its own wire code.

Every one of these is a 401, and the status alone therefore says almost nothing.
The codes are what let a client tell "rotate the token and retry" from "this
session is over" from "this account is disabled" — the distinction the 401 →
refresh → retry rotation is built on — without reading a message that will be
reworded and localized.
"""

from app.core.exception_handlers import UnauthorizedError


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
