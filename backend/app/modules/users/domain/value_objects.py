from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from app.modules.users.domain.errors import AdultAttestationRequired

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_NICKNAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,128}$")


class Authority(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        v = self.value.strip().lower()
        if len(v) > 320 or not _EMAIL_RE.match(v):
            raise ValueError(f"invalid email: {self.value!r}")
        object.__setattr__(self, "value", v)


@dataclass(frozen=True)
class Nickname:
    value: str

    def __post_init__(self) -> None:
        v = self.value.strip()
        if not (2 <= len(v) <= 64) or not _NICKNAME_RE.match(v):
            raise ValueError(f"invalid nickname: {self.value!r}")
        object.__setattr__(self, "value", v)


@dataclass(frozen=True)
class RawPassword:
    """The plaintext password as it arrives from the boundary.

    Carrying it as a value object keeps the strength rule co-located with the
    type and prevents accidentally hashing an unchecked string.
    """

    value: str

    def __post_init__(self) -> None:
        if not _PASSWORD_RE.match(self.value):
            raise ValueError(
                "password must be 8-128 chars with at least one letter and one digit"
            )


@dataclass(frozen=True)
class AdultAttestation:
    """The player's own claim that they are an adult, as a type.

    The platform is adults only and that is a precondition of *holding an
    account*, not a gate on who may be shown to whom (``docs/adr/0124``). The
    rule is enforced by making the attestation a thing you cannot hold unless it
    was given: the only value this constructs from is ``True``, so a
    registration that reaches ``User.register`` has one by construction and
    there is no path that defaults one into existence.

    **One boolean, and never a date of birth.** Nothing downstream asks *how
    old* — only *may they be here* — so a date would satisfy the rule by
    breaking the reason it exists, and the candidate index asserts its absence
    at build time. **This is not age verification** and claims to be nothing of
    the sort: it records that the question was asked and answered.

    It refuses with a typed error rather than the ``ValueError`` its neighbours
    raise, because a refused attestation is a sentence the player has to be
    shown, and the client chooses that sentence from a code (``docs/adr/0022``).
    A malformed email is a form the app already refuses before a round trip; an
    unticked box that reached the server is the one this has to name.
    """

    value: bool

    def __post_init__(self) -> None:
        if self.value is not True:
            raise AdultAttestationRequired()


@dataclass(frozen=True)
class HashedPassword:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("hashed password must not be empty")
