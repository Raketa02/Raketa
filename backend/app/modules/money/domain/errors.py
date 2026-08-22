"""Money errors.

No route mounts this context in v1 — the ledger is written by the outbox and by
inbound reports, and the one thing it puts on a screen is the debt line, which
rides on ``GET /api/v1/now`` (ADR-0058, ``Raketa02/Raketa#92``). They carry a
status and a code anyway, for the reason ``app/shared/domain/errors.py`` gives:
a status held in a separate registry is one a new subclass can be added
without, and the miss is a 500 in production rather than a red test.

**Every one of these is a refusal to write, never a repair.** The ledger is the
one place in Raketa where the record *is* the answer to a dispute (ADR-0055), so
a movement that does not belong is rejected at the door and the caller is told —
there is nothing here that quietly fixes an argument up and records it anyway.
"""

from __future__ import annotations

from app.shared.domain import BadRequestError, ConflictError


class MovementBelongsToAnotherPlayer(BadRequestError):
    """This movement names a player who is not this ledger's.

    The one rule that keeps *"no movement is homeless and none is written to two
    streams"* true (ADR-0055). Without it a movement naming Ania could be
    appended to Bartek's stream, and her balance would be the fold of whichever
    half anybody happened to read.
    """

    code = "money_movement_belongs_to_another_player"

    def __init__(self) -> None:
        super().__init__("That movement names a different player's ledger.")


class DuplicateMovementReference(ConflictError):
    """This ledger already holds a movement under that reference.

    A duplicate webhook is one of the three ways ADR-0057 says money gets
    recorded wrongly, and it is the only one of the three that is *detectable at
    the door*: the same reference arriving twice is the same event arriving
    twice. Refused rather than recorded and compensated, because a compensation
    is an admission that something happened, and nothing did.

    Unique **within a ledger**, which is what an aggregate can promise. Two
    players' movements sharing a reference is not a state this refuses, and it
    is not one anything downstream reads.
    """

    code = "money_duplicate_movement_reference"

    def __init__(self, reference: str) -> None:
        super().__init__(f"A movement under reference {reference} is already recorded.")


class LedgerAlreadyPseudonymised(ConflictError):
    """This ledger's player has already been erased.

    Refused rather than silently ignored: a second pseudonym would mean the
    ledger had two of them, and the read would name whichever the fold reached
    last — an identity question with two answers, which is exactly what
    pseudonymising is supposed to remove.
    """

    code = "money_ledger_already_pseudonymised"

    def __init__(self) -> None:
        super().__init__("This ledger's player has already been pseudonymised.")


class NothingToCompensate(BadRequestError):
    """No movement on this ledger carries the reference being corrected.

    A compensation that points at nothing is a movement with an amount, a
    direction and no story, and it would pass every other check.
    """

    code = "money_nothing_to_compensate"

    def __init__(self, reference: str) -> None:
        super().__init__(f"This ledger holds no movement under reference {reference}.")
