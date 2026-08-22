"""The Money context's domain events — one stream per player, append-only.

Two facts happen to a ledger: a movement is recorded, and the player behind it
is pseudonymised. There is no third, and there is deliberately no
``MovementCorrected``: ADR-0057 fixes that a wrong movement is corrected by a
**compensating movement**, so a correction is another ``MovementRecorded`` whose
reference is a ``REV-`` one. An event class for amending would be a shape the
ledger has no meaning for, and having it would be the invitation.

Events carry **primitive** fields — a party as its kind string and an optional
id, a cause as its ``str`` value, a reference as its printed text — so the wire
format survives whatever the Python types do later. ``parties.party_from`` and
``Reference.parse`` are the inverses, and each refuses what it did not write.

``player_id`` on the opening event is the ledger's **lookup key**: the stream id
is derived from it, so it is not needed to find the stream — it is there so a
stream can say whose it is without a table, exactly as ``RatingInitialised``
does. The reconciliation reads every ledger through the same door.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class MovementRecorded:
    """Money moved between two of the three parties, for a stated reason."""

    ledger_id: UUID
    player_id: UUID
    movement_id: UUID
    payer_kind: str
    payer_id: UUID | None
    payee_kind: str
    payee_id: UUID | None
    amount: int
    seat_match_id: UUID | None
    seat_index: int | None
    reservation_id: UUID | None
    reference: str
    cause: str
    occurred_at: datetime


@dataclass(frozen=True)
class PlayerPseudonymised:
    """The player behind this ledger asked to be forgotten, and was not.

    Accounting records carry a legal-obligation basis that survives an erasure
    request (ADR-0055), so **the movements stand**: the amounts, the causes and
    the references are exactly what they were. What changes is the party every
    reader of this ledger sees from here on — an opaque id that identifies
    nobody once Users has erased what does.
    """

    ledger_id: UUID
    player_id: UUID
    pseudonym: UUID
    occurred_at: datetime
