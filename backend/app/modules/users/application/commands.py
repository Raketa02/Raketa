from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RegisterUserCommand:
    """Credentials and the attestation — and nothing about who the player is
    (``docs/adr/0199`` §3). The nickname is asked in onboarding, with
    :class:`NameUserCommand`."""

    email: str
    password: str
    #: The player's own claim that they are an adult — the precondition of
    #: holding an account at all (``docs/adr/0124``). A plain ``bool`` here and
    #: a refusal in the handler, rather than an already-validated type, because
    #: a command is what a caller *asked for*: the boundary must be able to
    #: express the answer that gets refused, or the refusal has nowhere to
    #: happen. One boolean, and never a date of birth.
    adult_attested: bool


@dataclass(frozen=True)
class NameUserCommand:
    """The naming: the nickname people see this player by
    (``docs/adr/0199`` §3).

    For the authenticated player — the route supplies ``user_id`` from the
    session and never from the body. A plain string here for the reason
    ``adult_attested`` above is a plain ``bool``: a command is what a caller
    *asked for*, and the value object refuses inside the handler.
    """

    user_id: UUID
    nickname: str
