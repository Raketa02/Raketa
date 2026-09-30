"""What a caller asks the Payments context for, in the primitives it asked in."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AcceptPaymentTermsCommand:
    """The player accepted the payment terms they were shown.

    ``terms_version`` names the words on their screen; ``ip`` is the address
    the request came from, recorded beside the acceptance as its evidence — the
    route's, never the body's, since a client that could say where a consent was
    given could say one was given that never was."""

    player_id: UUID
    terms_version: str
    ip: str | None
