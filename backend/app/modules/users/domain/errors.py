from app.shared.domain import BadRequestError, ConflictError, UnauthorizedError


class AdultAttestationRequired(BadRequestError):
    """Nobody answered the one question an account is a precondition of.

    A 400 and not a 409: the request is incomplete, not in conflict with
    anything already stored. The code names an *attestation* rather than an age
    because there is no age anywhere in this system to be short of
    (``docs/adr/0124``) — what is missing is the claim, and the claim is all
    that is ever recorded.

    ``details.field`` puts the sentence the client chooses under the control
    that takes the answer, the way the two signup conflicts already do.
    """

    code = "adult_attestation_required"

    def __init__(self) -> None:
        super().__init__(
            "registration requires an adult attestation",
            details={"field": "adult_attested"},
        )


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
