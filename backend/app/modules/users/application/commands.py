from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RegisterUserCommand:
    """Credentials and the attestation — and nothing about who the player is
    (``docs/adr/0171`` §2). The name and the nickname are asked in onboarding,
    with :class:`NameUserCommand`."""

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
    """The naming: how people should see this player (``docs/adr/0171`` §2).

    One act carrying both values, for the authenticated player — the route
    supplies ``user_id`` from the session and never from the body. Plain strings
    here for the reason ``adult_attested`` above is a plain ``bool``: a command
    is what a caller *asked for*, and the value objects refuse inside the
    handler.
    """

    user_id: UUID
    name: str
    nickname: str


@dataclass(frozen=True)
class SetTesterMarkCommand:
    """Mark a player as a Tester, or clear the mark (``docs/adr/0180`` §9).

    ``player`` is **an account id or an email, as the operator typed it** — the
    admin command takes either, and resolving which one it is belongs to the use
    case, so the command line and a test ask one question. ``tester`` is the mark
    wanted, and asking for the one already held is admitted and records nothing.
    """

    player: str
    tester: bool
