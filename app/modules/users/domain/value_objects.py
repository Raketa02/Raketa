from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

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
class HashedPassword:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("hashed password must not be empty")
