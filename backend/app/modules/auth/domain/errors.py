from app.core.exception_handlers import UnauthorizedError


class InvalidCredentials(UnauthorizedError):
    def __init__(self) -> None:
        # Identical message on email-not-found vs wrong-password — no enumeration.
        super().__init__("invalid email or password")


class AccountDisabled(UnauthorizedError):
    def __init__(self) -> None:
        super().__init__("account disabled")


class InvalidRefreshToken(UnauthorizedError):
    def __init__(self, message: str = "invalid refresh token") -> None:
        super().__init__(message)


class RefreshTokenExpired(UnauthorizedError):
    def __init__(self) -> None:
        super().__init__("refresh token expired")


class RefreshTokenRevoked(UnauthorizedError):
    def __init__(self) -> None:
        super().__init__("refresh token has been revoked")


class RefreshTokenNotRecognised(UnauthorizedError):
    def __init__(self) -> None:
        super().__init__("refresh token not recognised")


class RefreshTokenMismatch(UnauthorizedError):
    def __init__(self) -> None:
        super().__init__("refresh token does not match")
