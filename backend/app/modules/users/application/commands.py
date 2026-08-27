from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterUserCommand:
    email: str
    nickname: str
    password: str
    #: The player's own claim that they are an adult — the precondition of
    #: holding an account at all (``docs/adr/0124``). A plain ``bool`` here and
    #: a refusal in the handler, rather than an already-validated type, because
    #: a command is what a caller *asked for*: the boundary must be able to
    #: express the answer that gets refused, or the refusal has nowhere to
    #: happen. One boolean, and never a date of birth.
    adult_attested: bool
