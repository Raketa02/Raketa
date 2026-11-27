"""The 8-character code a person types, and why it is **derived from the link**.

Every one-time credential is a link token and a code, issued together
(``docs/adr/0184`` §3). The token is 256 random bits, carried in a URL and never
typed. The code is what a person reads off an email on one device and types on
another — so it is short, upper-case, and written in an alphabet with **no
look-alikes**: no ``0``/``O``, no ``1``/``I``/``L``.

**The code is a function of the token**, not a second random draw. The public
invitation page shows the code to whoever opened its link
(``docs/adr/0186`` §3: *after you install, open Rakieta and enter this code*),
and both are stored only as hashes — so the one way to show a code the server
cannot read back is to recompute it from the token the reader is holding. That
costs nothing it protects: whoever holds the token can already use it, and the
code says nothing about the token in return. The derivation is domain-separated
and versioned in its prefix, so a later change is a new prefix rather than a
silent reinterpretation of every code already sent.

A typed code is forgiven its case and its spaces and dashes — a person copying
``K7M4 QX2P`` off a phone screen has typed the code — and nothing else.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Final

#: Thirty-one characters: the upper-case alphabet and the digits, less the
#: look-alikes. The group link's alphabet in upper case (``docs/adr/0183`` §4),
#: because a code is read aloud and typed, and upper case is what reads.
CODE_ALPHABET: Final = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

#: Eight characters: about forty bits, which five attempts per credential and a
#: lifetime of hours bound for any single guesser (``docs/adr/0184``, *Harder*).
CODE_LENGTH: Final = 8

_DERIVATION: Final = b"rakieta/one-time-code/v1:"


def code_for(token: str) -> str:
    """The code that goes out beside ``token``, and that ``token`` recomputes."""

    digest = int.from_bytes(
        hashlib.sha256(_DERIVATION + token.encode("utf-8")).digest(), "big"
    )
    characters = []
    for _ in range(CODE_LENGTH):
        digest, index = divmod(digest, len(CODE_ALPHABET))
        characters.append(CODE_ALPHABET[index])
    return "".join(characters)


@dataclass(frozen=True)
class TypedCode:
    """A code as a person typed it, read the way it was written: upper case,
    with the spaces and dashes they put in to read it taken out again.

    Nothing else is refused here: a typed code of the wrong length or outside
    the alphabet is simply not the code that was sent, and is told so as every
    other wrong code is."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "value", "".join(self.value.split()).replace("-", "").upper()
        )
