from app.core.exception_handlers import ConflictError, UnauthorizedError


class EmailAlreadyRegistered(ConflictError):
    def __init__(self) -> None:
        super().__init__("email already registered", details={"field": "email"})


class NicknameAlreadyTaken(ConflictError):
    def __init__(self) -> None:
        super().__init__("nickname already taken", details={"field": "nickname"})


class UserNotEligible(UnauthorizedError):
    def __init__(self) -> None:
        super().__init__("user no longer eligible")


class InactiveUserCannotBePromoted(ConflictError):
    def __init__(self) -> None:
        super().__init__("inactive user cannot be promoted")
