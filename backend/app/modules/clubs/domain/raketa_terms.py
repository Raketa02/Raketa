"""How a club works with Raketa, and the settings that go with it (the
mechanics §16.3, §16.6, §16.15; ``docs/adr/0189`` §3).

**One way of working for the whole club** — Only Raketa, Instant or On request
— and it is what a court hour's **book-by** is derived from: the release time
at an Only Raketa club, the start less the minimum notice at the other two.
Nobody chooses a book-by; ``book_by`` is where it is derived, once, so a card
and the hours a club can sell cannot disagree about when one stops.

**Every bound here is domain, never configuration.** Each is a range the desk's
form offers, not a threshold anything is tuned against, and each one is chosen
so that no combination of settings is contradictory: the longest time to
confirm is an hour and the shortest minimum notice is an hour, so an On request
club's answer is always due before its game could start.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final, final

from app.kernel import Instant, hours, minutes, shifted
from app.modules.clubs.domain.errors import SettingOutOfRange


class WayOfWorking(StrEnum):
    """How a club sells through Raketa (the mechanics §16.3)."""

    #: Raketa sells the club's Raketa hours alone, until the release time.
    ONLY_RAKETA = "ONLY_RAKETA"
    #: Both sell; a Raketa booking is final, and the club closes what it sells
    #: elsewhere.
    INSTANT = "INSTANT"
    #: Both sell; the club confirms each full game within its time to confirm,
    #: and nobody pays until it does.
    ON_REQUEST = "ON_REQUEST"


#: Days before a game an Only Raketa club's unsold hours return to it. At least
#: one, and short of the fourteen days a deck looks ahead, or nothing would sell.
RELEASE_LEAD_DAYS: Final = (1, 13)
#: Hours before a game a player may leave free. Nought is *free until the start*.
CUT_OFF_HOURS: Final = (0, 72)
#: Hours before a game the latest Raketa booking lands (Instant, On request).
MINIMUM_NOTICE_HOURS: Final = (1, 48)
#: Minutes an On request club has to answer a full game. **Never more than the
#: shortest minimum notice**, so the answer is always due before the start.
TIME_TO_CONFIRM_MINUTES: Final = (5, 60)
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
    """*Offer our groups other clubs' courts when ours are full*: off by
    default, and within 10 km when on (the mechanics §4.3). The distance is
    kept while it is off, so switching it back on restores it. Its range is
    refused by ``RaketaSettings``, in the form's order."""

    offered: bool = False
    within_km: int = 10


@final
@dataclass(frozen=True, slots=True)
class RaketaSettings:
    """The settings a club confirms, **each at its default until it does**
    (the mechanics §16.6). A changed setting applies to games booked after the
    change; a booked game keeps the cut-off it was booked with."""

    release_lead_days: int = 3
    cut_off_hours: int = 24
    minimum_notice_hours: int = 2
    time_to_confirm_minutes: int = 30
    other_clubs_courts: OtherClubsCourts = field(default_factory=OtherClubsCourts)
    check_in: bool = False

    def __post_init__(self) -> None:
        # In the form's order, so the first refusal is the first field read.
        _within(self.release_lead_days, RELEASE_LEAD_DAYS, named="release_lead_days")
        _within(self.cut_off_hours, CUT_OFF_HOURS, named="cut_off_hours")
        _within(
            self.minimum_notice_hours,
            MINIMUM_NOTICE_HOURS,
            named="minimum_notice_hours",
        )
        _within(
            self.time_to_confirm_minutes,
            TIME_TO_CONFIRM_MINUTES,
            named="time_to_confirm_minutes",
        )
        _within(
            self.other_clubs_courts.within_km,
            OTHER_CLUBS_KM,
            named="other_clubs_courts",
        )


def book_by(start: Instant, *, way: WayOfWorking, settings: RaketaSettings) -> Instant:
    """The latest moment a game on the court hour from ``start`` can still
    fill (the mechanics §5.4): the release time at an Only Raketa club, the
    start less the minimum notice at the other two.

    **Elapsed time, never wall-clock subtraction** (``shifted``): three days
    before a Sunday game across a clock change is seventy-two hours.
    """

    if way is WayOfWorking.ONLY_RAKETA:
        return shifted(start, minutes(-settings.release_lead_days * _MINUTES_PER_DAY))
    return shifted(start, hours(-settings.minimum_notice_hours))
