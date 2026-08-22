"""What a movement is called on a statement: ``PAY-…``, ``REF-…``, ``REV-…``.

ADR-0034's table lists the three prefixes as the ledger's reference vocabulary,
and ADR-0057 reserves ``REV-`` for the one thing that is not a payment or a
refund: **a correction**. Nothing here is display copy — a reference is an
identifier a support agent reads back to a player and a bank, and the prefix is
part of it.

**The kind is a prefix and not a second field beside a free string**, because
the two would be able to disagree: a ``REV-…`` text sitting on a movement whose
kind said *payment* is a compensation nothing counts as one, and the
reconciliation reads compensations by kind. One fact, one spelling, and
``parse`` is its inverse so a stored text comes back as the same value.

**A VAT invoice number is not a reference.** ADR-0034's table lists
``FV/2026/08/118`` beside these three; invoicing is out of Money's scope
(ADR-0055) and a fourth kind here would be the first brick of it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import final

from app.kernel import invariant

#: Letters and digits. Deliberately no hyphen: the prefix is separated by one,
#: so a token containing one would make ``parse`` ambiguous about where the kind
#: ends — and an identifier that cannot be read back is not an identifier.
_TOKEN = re.compile(r"^[A-Za-z0-9]+$")


class ReferenceKind(str, Enum):
    """The three prefixes, which are also the three things a movement can be."""

    #: Money going out of a player's hands.
    PAYMENT = "PAY"
    #: Money going back to them.
    REFUND = "REF"
    #: A correction of a movement that was wrong. Never an amendment: the
    #: original stands and this one compensates it (ADR-0057).
    REVERSAL = "REV"


@final
@dataclass(frozen=True)
class Reference:
    """One movement's identifier: a kind, and a token unique within it."""

    kind: ReferenceKind
    token: str

    def __post_init__(self) -> None:
        invariant(
            bool(_TOKEN.match(self.token)),
            f"a reference token that is not letters and digits: {self.token!r}",
        )

    @property
    def text(self) -> str:
        """What is printed, stored and read back to a player."""

        return f"{self.kind.value}-{self.token}"

    @property
    def is_compensation(self) -> bool:
        """Whether this movement exists to correct another one."""

        return self.kind is ReferenceKind.REVERSAL

    @classmethod
    def parse(cls, text: str) -> "Reference":
        """The inverse of ``text``. Refuses anything it did not write."""

        prefix, separator, token = text.partition("-")
        invariant(separator == "-", f"a reference with no prefix: {text!r}")
        invariant(
            prefix in {kind.value for kind in ReferenceKind},
            f"a reference under an unknown prefix: {text!r}",
        )
        return cls(kind=ReferenceKind(prefix), token=token)
