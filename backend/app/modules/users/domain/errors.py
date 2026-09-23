from app.shared.domain import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    UnauthorizedError,
)


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


class UnknownPlayer(NotFoundError):
    """No account answers to the reference an admin command was given.

    Raised by ``SetTesterMark``, which takes an account id **or** an email as
    typed (``docs/adr/0180`` §9). One refusal for every way of naming nobody —
    an address nobody registered, an id with no account behind it, and a string
    that is neither — because to the operator reading it all three are the same
    typo. No route raises it today; the status is the taxonomy's, so the day one
    does it is a 404 rather than a 500.
    """

    code = "unknown_player"

    def __init__(self, reference: str) -> None:
        super().__init__(
            f"no account answers to {reference!r}", details={"player": reference}
        )
