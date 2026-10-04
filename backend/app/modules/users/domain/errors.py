from app.shared.domain import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
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
            "an adult attestation is required",
            details={"field": "adult_attested"},
        )


class AdultAttestationMissing(ForbiddenError):
    """This account has not given the Adult attestation, and **playing
    requires it** (``docs/adr/0185`` §5): no Skill rating and no Player profile
    begins for an account that has not attested.

    Every sign-up attested, so this is met only by an account an Invitation
    opened, before *Start playing*'s first step — or by a client that skipped
    it. A 403 and not the sign-up's 400: nothing is missing from the request;
    the account has not yet done what the act requires. The way on is
    ``POST /users/me/adult-attestation``.
    """

    code = "adult_attestation_missing"

    def __init__(self) -> None:
        super().__init__("playing requires the adult attestation first")


class EmailInvalid(BadRequestError):
    """:class:`Email` refused an address, for a caller that has to name the field.

    ``Email`` itself raises ``ValueError``, which is right for an invariant and
    a 500 for a typo (``CONTEXT.md``, *Invariant vs Unavailability*). A form that
    takes an address from a person raises this instead, with ``details.field``
    under the control that took it. **The club's sign-up is the only one today**
    (``docs/adr/0182`` §3); the player's refuses a malformed address at its
    schema, as a ``422``, before ``Email`` is reached.
    """

    code = "email_invalid"

    def __init__(self) -> None:
        super().__init__("invalid email address", details={"field": "email"})


class PasswordTooWeak(BadRequestError):
    """:class:`RawPassword` refused a password, for a caller that has to name
    the field — **the same rule for every account** (``docs/adr/0182`` §3).

    **Raised by the club's sign-up only.** The player's sign-up bounds the
    length at its schema and does not catch the rest of the rule, so a
    sixteen-letter password with no digit still reaches ``RawPassword`` there as
    a ``ValueError``. Here beside the rule so that fixing that path is one
    ``except`` rather than a second code.
    """

    code = "password_too_weak"

    def __init__(self) -> None:
        super().__init__(
            "password must be 8-128 chars with at least one letter and one digit",
            details={"field": "password"},
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
