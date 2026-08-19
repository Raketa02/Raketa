"""Pairing, version 1.

The balance forecast at either arity, for a full match and a forming one: the
Protocol, the snapshot value objects, the roster with its imputed seats, the
folded-normal arithmetic, the one clamp, the one rounding, and in doubles the three
splits ranked on the expected gap. Plus what a forming match says about the seats it
has not filled — the seat target, solved rather than scanned, and the target band it
falls back to, which is also where every stand-in is drawn from.

This is the whole of the pairing half of the matchmaking spec. What is left in it is
Match Fit, which is a separate engine with its own version lineage and reads this
one's output as an input.
"""

from app.engines.pairing.v1.constants import (
    CONSTANTS,
    ENGINE_VERSION,
    PAIRED_SPORTS,
    PairingConstants,
)
from app.engines.pairing.v1.engine import PairingEngineV1

__all__ = [
    "CONSTANTS",
    "ENGINE_VERSION",
    "PAIRED_SPORTS",
    "PairingConstants",
    "PairingEngineV1",
]
