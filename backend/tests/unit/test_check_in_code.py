"""A player's check-in code — what the desk scans on the day (#542; the mechanics
§15.1; the screens A4.1).

**Derived, never stored**: one keyed digest of the booking and the player, so the
phone can be shown it on every read and the club's desk (#547) can recompute it,
and nothing holding it ever reaches the event store or the outbox
(``docs/adr/0184`` §4). A short code to type and a QR payload to scan, which
carries the booking and the player beside the same code.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from app.kernel import instant
from app.modules.bookings.domain.check_in import (
    CHECK_IN_CODE_LENGTH,
    check_in_code,
    is_the_game_day,
)
from app.modules.auth.domain.credential_code import CODE_ALPHABET

BOOKING = UUID("6b2d3a1e-6f58-4c2e-9a3b-0f2a1d7c9e11")
OLA = UUID("0d6a1c4b-2f8e-4a71-b0c3-5e9d8f7a6b21")
KUBA = UUID("1f2e3d4c-5b6a-4987-8a6b-5c4d3e2f1a03")
KEY = b"the server's own key"
WARSAW = ZoneInfo("Europe/Warsaw")


def warsaw(day: int, hour: int, minute: int = 0):
    return instant(datetime(2026, 10, day, hour, minute, tzinfo=WARSAW))


def test_a_code_is_short_and_typed_from_an_alphabet_with_no_look_alikes():
    code = check_in_code(booking_id=BOOKING, player_id=OLA, key=KEY)

    assert len(code.short_code) == CHECK_IN_CODE_LENGTH == 6
    assert set(code.short_code) <= set(CODE_ALPHABET)


def test_the_same_seat_is_the_same_code_on_every_read():
    first = check_in_code(booking_id=BOOKING, player_id=OLA, key=KEY)
    again = check_in_code(booking_id=BOOKING, player_id=OLA, key=KEY)

    assert first == again


def test_every_seat_on_a_booking_has_its_own_code():
    ola = check_in_code(booking_id=BOOKING, player_id=OLA, key=KEY)
    kuba = check_in_code(booking_id=BOOKING, player_id=KUBA, key=KEY)

    assert ola.short_code != kuba.short_code


def test_nobody_without_the_key_can_compute_a_code():
    """A partner knows the booking and every id on it; without the server's key
    they still cannot make somebody else's code — so a code at the desk is that
    player's phone, not a guess."""

    ours = check_in_code(booking_id=BOOKING, player_id=OLA, key=KEY)
    theirs = check_in_code(booking_id=BOOKING, player_id=OLA, key=b"another key")

    assert ours.short_code != theirs.short_code


def test_the_qr_names_the_booking_the_player_and_the_code():
    """What the desk scans says which seat it is for, so a code for another club
    or another day can be told apart from a wrong one (#547)."""

    code = check_in_code(booking_id=BOOKING, player_id=OLA, key=KEY)

    assert code.qr_payload == f"RAKETA-CHECK-IN:1:{BOOKING}:{OLA}:{code.short_code}"


def test_the_game_day_is_the_clubs_calendar_day_of_the_hour():
    game = warsaw(10, 17)

    assert is_the_game_day(game, now=warsaw(10, 0, 1))
    assert is_the_game_day(game, now=warsaw(10, 23, 59))
    assert not is_the_game_day(game, now=warsaw(9, 23, 59))
    assert not is_the_game_day(game, now=warsaw(11, 0, 0))


def test_an_early_hour_is_on_the_day_in_krakow_not_in_utc():
    """07:00 in Kraków is 05:00 UTC the same day, and 00:30 there is the evening
    before in UTC — the day is the club's."""

    game = warsaw(10, 7)

    assert is_the_game_day(game, now=warsaw(10, 0, 30))
