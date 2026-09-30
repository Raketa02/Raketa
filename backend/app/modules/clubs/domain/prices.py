"""What a court-hour costs, per sport, and the share a player pays of it (the
mechanics §16.5, the screens B3).

**Money is integer grosze**, and this is where it first crosses the wire since
the reset took the kernel's money module away (``docs/value-formatting.md``):
an integer, because a share is charged to the grosz and a float is how a grosz
goes missing; grosze, because that is the unit the charge is made in.

**A standard price per court-hour, and optional bands** — weekdays or the
weekend, between two hours — that price the hours they cover differently
(*Weekdays 17:00–22:00 · 140 zł*). Bands of the same days may not overlap, so an
hour has one price and nobody has to know which band wins.

**The share is the price divided by the seats, and it is exact.** It is what a
player pays and it is fixed on the card, so it has to be a whole number of
grosze: a price that does not split among the sport's seats is refused rather
than rounded, because rounding would hand a grosz to somebody — the club, or a
player — that nobody agreed to. A price in whole złoty always splits.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise
from typing import Final, final

from app.kernel import SPORT_SPECS, IsoWeekday, Sport
from app.modules.clubs.domain.court_hours import within_the_day
from app.modules.clubs.domain.errors import (
    PriceBandHoursInvalid,
    PriceBandsOverlap,
    PriceDoesNotSplit,
    PriceOutOfRange,
    PriceSportNotOffered,
    PriceSportRepeated,
)
from app.modules.player_profile.domain.weekly_hours import WEEKEND_DAYS

#: The cheapest court-hour, in grosze — 10 zł. **Domain, never configuration.**
#: A floor under a typo rather than a market judgement: nothing in Poland sells
#: an hour for less, and a share below it is one a card charge would not cover.
COURT_HOUR_PRICE_LEAST: Final = 10_00

#: The dearest court-hour, in grosze — 1 000 zł. A ceiling over a typo (a price
#: entered in grosze twice over), not a limit anybody is meant to meet.
COURT_HOUR_PRICE_MOST: Final = 1000_00


class BandDays(StrEnum):
    """Which days a band prices: Monday to Friday, or Saturday and Sunday."""

    WEEKDAYS = "WEEKDAYS"
    WEEKEND = "WEEKEND"

    @classmethod
    def of(cls, day: IsoWeekday) -> "BandDays":
        return cls.WEEKEND if int(day) in WEEKEND_DAYS else cls.WEEKDAYS


def seats(sport: Sport) -> int:
    """How many players a game of this sport seats — the registry's number."""

    return SPORT_SPECS[sport].players


def share_of(price_grosze: int, sport: Sport) -> int:
    """The share of a court-hour one player pays. **Exact, by construction**:
    a price is refused unless it splits (``SportPrices``)."""

    return price_grosze // seats(sport)


@final
@dataclass(frozen=True, slots=True)
class PriceBand:
    """A price for the hours from ``opens`` until ``closes`` on these days."""

    days: BandDays
    opens: int
    closes: int
    grosze: int

    def holds(self, day: IsoWeekday, hour: int) -> bool:
        return BandDays.of(day) == self.days and self.opens <= hour < self.closes

    @property
    def code(self) -> str:
        """The band as one string, which is how a stream stores it —
        ``"WEEKDAYS:17:22:14000"`` — for the reason a week's cell is a code."""

        return f"{self.days.value}:{self.opens}:{self.closes}:{self.grosze}"

    @classmethod
    def from_code(cls, code: str) -> "PriceBand":
        days, opens, closes, grosze = code.split(":")
        return cls(
            days=BandDays(days),
            opens=int(opens),
            closes=int(closes),
            grosze=int(grosze),
        )

    @property
    def sort_key(self) -> tuple[int, int]:
        return (0 if self.days is BandDays.WEEKDAYS else 1, self.opens)


@final
@dataclass(frozen=True, slots=True)
class SportPrices:
    """One sport's prices: the standard court-hour, and its bands in one
    canonical order — weekdays first, then by the hour they open.

    Refused, **naming the sport**, when a price is out of range or does not
    split among its seats, a band's hours are not within 07:00–23:00 or open
    no later than they close, or two bands of the same days overlap.
    """

    sport: Sport
    grosze: int
    bands: tuple[PriceBand, ...] = ()

    def __post_init__(self) -> None:
        for price in (self.grosze, *(band.grosze for band in self.bands)):
            if not COURT_HOUR_PRICE_LEAST <= price <= COURT_HOUR_PRICE_MOST:
                raise PriceOutOfRange(
                    sport=self.sport.value,
                    least=COURT_HOUR_PRICE_LEAST,
                    most=COURT_HOUR_PRICE_MOST,
                )
            if price % seats(self.sport):
                raise PriceDoesNotSplit(sport=self.sport.value, seats=seats(self.sport))
        for band in self.bands:
            if not within_the_day(band.opens, band.closes):
                raise PriceBandHoursInvalid(sport=self.sport.value)
        ordered = tuple(sorted(self.bands, key=lambda band: band.sort_key))
        for earlier, later in pairwise(ordered):
            if earlier.days == later.days and later.opens < earlier.closes:
                raise PriceBandsOverlap(sport=self.sport.value)
        object.__setattr__(self, "bands", ordered)

    @property
    def share(self) -> int:
        return share_of(self.grosze, self.sport)

    def price_at(self, day: IsoWeekday, hour: int) -> int:
        """What the court-hour starting at ``hour`` on ``day`` costs: the band
        that holds it, or the standard price. At most one band can."""

        for band in self.bands:
            if band.holds(day, hour):
                return band.grosze
        return self.grosze


def price_table(
    rows: Iterable[tuple[Sport, int, tuple[PriceBand, ...]]],
    *,
    offered_sports: Collection[Sport],
) -> tuple[SportPrices, ...]:
    """The table a save describes, refused **row by row in the order sent**:
    first whether the club offers the sport and has not priced it already in
    this save, then its prices. Each row is a sport, its standard price in
    grosze, and its bands."""

    table: list[SportPrices] = []
    for sport, grosze, bands in rows:
        if sport not in offered_sports:
            raise PriceSportNotOffered(sport=sport.value)
        if any(priced.sport == sport for priced in table):
            raise PriceSportRepeated(sport=sport.value)
        table.append(SportPrices(sport=sport, grosze=grosze, bands=bands))
    return tuple(table)
