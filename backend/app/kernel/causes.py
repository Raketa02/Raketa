"""Why money moved, and why a match ended, in five names and no more.

ADR-0057 fixed that *every movement names the rule that caused it*, and left the
list knowingly short; ADR-0073's walk across the thirty-six cards is where it was
finished. These are the five, and the enumeration is **closed** — a sixth arrives
as a decision somebody made in a diff, the same way a seventh act does
(``docs/adr/0083-a-card-names-one-act-and-twenty-seven-name-none.md``).

**Four names, three identical money rules.** ``INVENTORY_LOST``,
``CLUB_CANCELLED`` and ``FORM_CANCELLED`` all return money to the method it came
from; ``CHECKPOINT_CANCELLED`` issues club credit
(``docs/adr/0058-one-balance-and-it-never-goes-above-zero.md``). They are four
names because they are four different sentences to the player, not four
different arithmetics — and *refunded* alone answers nothing a year later, which
is the whole reason causes exist.

**``SETTLEMENT_REOPENED`` never appears on a card**, because by the time a
settled departure is reopened no card exists. It is a ledger cause only, and it
is in the enumeration rather than beside it because a cause the ledger may write
and the enumeration may not name is the same defect in the other direction.

**It lives in the kernel because a second implementation of it would be a
defect** — ADR-0022's own test. Matches produces the cause, Money records it and
Now renders it; three contexts reading one list verbatim is what the innermost
ring is for. It is deliberately **not** in ``money.py``: three of the five are
match endings that happen to move money, and filing them under the arithmetic
would make the next reader look for a cancellation in the wrong place.
"""

from __future__ import annotations

from enum import Enum

from app.kernel.invariants import invariant


class Cause(str, Enum):
    """The rule that fired, never who was watching.

    A cause is the same cause for all three of a card's audiences
    (``docs/adr/0072-two-sentences-are-two-situations-and-a-leaver-is-a-third-audience.md``):
    it names what happened to the *match*, and the sentence each audience reads
    about it is the client's.
    """

    #: The club sold the court out from under a forming match.
    INVENTORY_LOST = "inventoryLost"
    #: The club cancelled the match itself.
    CLUB_CANCELLED = "clubCancelled"
    #: The match never reached the format it was sold as.
    FORM_CANCELLED = "formCancelled"
    #: The match was still short at its checkpoint. Club credit, not a refund.
    CHECKPOINT_CANCELLED = "checkpointCancelled"
    #: A settled departure was reopened. A ledger cause; it reaches no card.
    SETTLEMENT_REOPENED = "settlementReopened"


#: Pinned rather than counted, so that a member arriving or leaving is a decision
#: somebody made in a diff — the rule ``SITUATION_COUNT`` already holds one ring
#: out from here.
CAUSE_COUNT = 5

invariant(
    len(Cause) == CAUSE_COUNT,
    f"the enumeration names {len(Cause)} causes, not {CAUSE_COUNT}",
)
