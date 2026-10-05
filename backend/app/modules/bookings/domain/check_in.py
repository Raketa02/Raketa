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

**The desk reads what it is handed** (#547): a scan is the whole payload — the
booking, the player and the code — and a typed code is the six characters,
however the desk spaced or cased them. Either is a seat's only when the digest
agrees, compared in constant time.
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


@final
@dataclass(frozen=True, slots=True)
class ReadCode:
    """What the desk was handed, read: the short code, and — from a scan — the
    booking and the player it names."""

    short_code: str
    booking_id: UUID | None = None
    player_id: UUID | None = None

    def is_of(self, code: CheckInCode) -> bool:
        """Whether this is that seat's code."""

        return hmac.compare_digest(self.short_code, code.short_code)


#: What a desk may put between characters of a typed code.
_SEPARATORS: Final = str.maketrans("", "", " -")


def read_code(text: str) -> ReadCode | None:
    """A scanned payload or a typed code — ``None`` for anything that is
    neither, which is no seat's at all."""

    trimmed = text.strip()
    if trimmed.upper().startswith("RAKETA-CHECK-IN:"):
        return _scanned(trimmed)
    typed = trimmed.translate(_SEPARATORS).upper()
    if not _a_short_code(typed):
        return None
    return ReadCode(short_code=typed)


def _scanned(payload: str) -> ReadCode | None:
    prefix, _, rest = payload.rpartition(":")
    head, _, player = prefix.rpartition(":")
    version, _, booking = head.rpartition(":")
    if version.upper() != _QR_PREFIX or not _a_short_code(rest.upper()):
        return None
    try:
        return ReadCode(
            short_code=rest.upper(), booking_id=UUID(booking), player_id=UUID(player)
        )
    except ValueError:
        return None


def _a_short_code(text: str) -> bool:
    return len(text) == CHECK_IN_CODE_LENGTH and all(
        character in CODE_ALPHABET for character in text
    )
