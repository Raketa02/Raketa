"""``CheckInCodes`` under the server's own key (#542; the mechanics §15.1).

**The key is derived from the platform's signing secret**, domain-separated by
its own prefix, rather than a setting of its own: the secret is already
required, kept out of every log and refused at its shipped default in
production (``app/core/config.py``), and a check-in code is a short-lived thing
shown fresh on every read of the game — so rotating the secret, which signs
everybody out anyway, only changes the codes phones show the next time they
look. A separate setting can replace it without changing a code's shape.
"""

from __future__ import annotations

import hashlib
from typing import Final, final
from uuid import UUID

from app.modules.bookings.domain.check_in import CheckInCode, check_in_code

_KEY_DERIVATION: Final = b"raketa/check-in-key/v1:"


@final
class KeyedCheckInCodes:
    def __init__(self, secret: str) -> None:
        self._key = hashlib.sha256(_KEY_DERIVATION + secret.encode("utf-8")).digest()

    def code_for(self, booking_id: UUID, player_id: UUID) -> CheckInCode:
        return check_in_code(booking_id=booking_id, player_id=player_id, key=self._key)
