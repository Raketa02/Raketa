from app.core.exception_handlers import ConflictError, UnauthorizedError


class EmailAlreadyRegistered(ConflictError):
    code = "email_already_registered"

    def __init__(self) -> None:
        super().__init__("email already registered", details={"field": "email"})


class NicknameAlreadyTaken(ConflictError):
    code = "nickname_already_taken"

    def __init__(self) -> None:
        super().__init__("nickname already taken", details={"field": "nickname"})


class UserNotEligible(UnauthorizedError):
    code = "user_not_eligible"

    def __init__(self) -> None:
        super().__init__("user no longer eligible")


class InactiveUserCannotBePromoted(ConflictError):
    code = "inactive_user_cannot_be_promoted"

    def __init__(self) -> None:
        super().__init__("inactive user cannot be promoted")
