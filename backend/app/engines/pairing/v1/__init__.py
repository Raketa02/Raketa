"""Pairing, version 1.

The balance forecast for a singles match: the Protocol, the snapshot value
objects, the folded-normal arithmetic, the one clamp and the one rounding. The
three doubles splits, the seat target, the target band and seat imputation extend
this version rather than replacing it.
"""

from app.engines.pairing.v1.constants import CONSTANTS, ENGINE_VERSION, PairingConstants
from app.engines.pairing.v1.engine import PairingEngineV1

__all__ = ["CONSTANTS", "ENGINE_VERSION", "PairingConstants", "PairingEngineV1"]
