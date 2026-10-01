"""A player's check-in code — what the club's desk scans on the day (#542; the
mechanics §15.1; ``docs/adr/0189`` §7).

**Derived, never stored.** A code is one keyed digest of the booking and the
seat's player, so the phone is shown it on every read of the game and the desk
(#547) recomputes it to see whose it is — and nothing holding it is written
anywhere: not the event store, not the outbox, not a projection
(``docs/adr/0184`` §4: a code is a secret, and a secret never enters either).
**The key is the server's**: everybody on a game knows its booking and every
player's id, and none of them can compute a partner's code without it — so a
code shown at the desk is that player's phone, never a guess.

**Two forms of one code.** The short code is what a desk types when the camera
will not read: six characters in the platform's typed-code alphabet, upper case
and without look-alikes. The QR payload is what it scans: the booking, the
player and the same code, so a code for another club or another day is told
apart from a wrong one (#547). The derivation and the payload are versioned in
their prefixes, so a later change is a new prefix rather than a silent
reinterpretation of every code a phone is showing.

**Two borrows, both pure**: the alphabet from ``auth/domain/credential_code.py``,
the one alphabet a person types a code in on this platform, and the club's
calendar from ``clubs/domain/court_hours.py``, where every court hour is read.

**On the day** is the club's calendar day of the game's hour — what *on the day*
means at a desk in Kraków, whatever the server's clock zone.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from app.kernel import Instant
from app.modules.auth.domain.credential_code import CODE_ALPHABET
from app.modules.clubs.domain.court_hours import local_day

#: Six characters: about thirty bits — enough that two seats at one club on one
#: day never share a code, and short enough to read off a phone at a desk.
CHECK_IN_CODE_LENGTH: Final = 6

_DERIVATION: Final = b"raketa/check-in/v1:"
_QR_PREFIX: Final = "RAKETA-CHECK-IN:1"


@final
@dataclass(frozen=True, slots=True)
class CheckInCode:
    """One seat's code: to type, and to scan."""

    short_code: str
    qr_payload: str


def check_in_code(*, booking_id: UUID, player_id: UUID, key: bytes) -> CheckInCode:
    """The code of ``player_id``'s seat on ``booking_id``, under the server's
    ``key`` — the same on every read, and different for every seat."""

    digest = hmac.new(
        key, _DERIVATION + booking_id.bytes + player_id.bytes, hashlib.sha256
    ).digest()
    remaining = int.from_bytes(digest, "big")
    characters = []
    for _ in range(CHECK_IN_CODE_LENGTH):
        remaining, index = divmod(remaining, len(CODE_ALPHABET))
        characters.append(CODE_ALPHABET[index])
    short_code = "".join(characters)
    return CheckInCode(
        short_code=short_code,
        qr_payload=f"{_QR_PREFIX}:{booking_id}:{player_id}:{short_code}",
    )


def is_the_game_day(start: Instant, *, now: Instant) -> bool:
    """Whether ``now`` falls on the club's calendar day of a game at ``start``."""

    return local_day(now) == local_day(start)
