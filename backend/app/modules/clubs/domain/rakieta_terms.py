"""A club's Rakieta settings, and the book-by they give each hour (the mechanics
§5.4, §16.3, §16.6, §16.15; ``docs/adr/0189`` §3, ``docs/adr/0196`` §1).

**One way of working: Only Rakieta, until Rakieta is the club's booking
software** (#670). The club hands Rakieta a block of hours, which Rakieta sells
alone until the **release time** — the release lead before each game — and a
court hour's **book-by** is that release time. Nobody chooses a book-by;
``book_by`` is where it is derived, once, so a card and the hours a club can
sell cannot disagree about when one stops. *Instant* and *On request*, with
the choice between the three, the minimum notice and the time to confirm,
were removed (#669, #670).

**Every bound here is domain, never configuration.** Each is a range the desk's
form offers, not a threshold anything is tuned against.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Final, final

from app.kernel import Instant, minutes, shifted
from app.modules.clubs.domain.errors import SettingOutOfRange


#: Days before a game a club's unsold hours return to it. At least one, and
#: short of the fourteen days a deck looks ahead, or nothing would sell. **So no
#: game fills later than a day before its start** — a call kept as decided
#: (``docs/adr/0196`` §7, call 1).
RELEASE_LEAD_DAYS: Final = (1, 13)
#: Hours before a game a player may leave free. Nought is *free until the start*.
CUT_OFF_HOURS: Final = (0, 72)
#: How far another club's court may be for this club's groups, in kilometres.
OTHER_CLUBS_KM: Final = (1, 50)

_MINUTES_PER_DAY: Final = 24 * 60


def _within(value: int, bounds: tuple[int, int], *, named: str) -> None:
    least, most = bounds
    if not least <= value <= most:
        raise SettingOutOfRange(field=named, least=least, most=most)


@final
@dataclass(frozen=True, slots=True)
class OtherClubsCourts:
    """*Offer our groups other clubs' courts when ours are full*: **on by
    default**, within 10 km (``docs/adr/0202`` §7; the mechanics §4.3) — an
    official group is offered other clubs within the distance at an hour its
    club has no free court, and only its club's while switched off. The
    distance is kept while it is off, so switching it back on restores it. Its
    range is refused by ``RakietaSettings``, in the form's order."""

    offered: bool = True
    within_km: int = 10


@final
@dataclass(frozen=True, slots=True)
class RakietaSettings:
    """The settings a club confirms, **each at its default until it does**
    (the mechanics §16.6). A changed setting applies to games booked after the
    change; a booked game keeps the cut-off it was booked with."""

    release_lead_days: int = 3
    cut_off_hours: int = 24
    other_clubs_courts: OtherClubsCourts = field(default_factory=OtherClubsCourts)

    def __post_init__(self) -> None:
        # In the form's order, so the first refusal is the first field read.
        _within(self.release_lead_days, RELEASE_LEAD_DAYS, named="release_lead_days")
        _within(self.cut_off_hours, CUT_OFF_HOURS, named="cut_off_hours")
        _within(
            self.other_clubs_courts.within_km,
            OTHER_CLUBS_KM,
            named="other_clubs_courts",
        )


def book_by(start: Instant, *, settings: RakietaSettings) -> Instant:
    """The latest moment a game on the court hour from ``start`` can still
    fill (the mechanics §5.4): **its release time**, the release lead before
    it — after which the hour is the club's again.

    **Elapsed time, never wall-clock subtraction** (``shifted``): three days
    before a Sunday game across a clock change is seventy-two hours.
    """

    return shifted(start, minutes(-settings.release_lead_days * _MINUTES_PER_DAY))


#: Longer than any book-by can be ahead of its hour — the longest release lead,
#: and a day.
_BEFORE_ANY_DEADLINE: Final = timedelta(days=RELEASE_LEAD_DAYS[1] + 1)


def before_any_deadline(start: Instant) -> Instant:
    """A moment early enough that what a club sells, read at it, holds every
    hour from ``start`` **whatever deadline its settings give the hour** — the
    reading a card's held court hour and a full game's free court are made at,
    since a card keeps the book-by it was made with (#540, #541)."""

    return start - _BEFORE_ANY_DEADLINE
