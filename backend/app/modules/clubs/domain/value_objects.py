"""What a club is: a name, a district, a city, its sports and a point.

Each value object normalises what it is given and refuses what it cannot hold
**with the field-level error the desk is shown** (``clubs/domain/errors.py``),
because every one of these is typed by a person into a form. The same objects
are rebuilt from a stream on replay, where nothing they refuse can appear.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

from app.kernel import Sport
from app.modules.clubs.domain.errors import (
    ClubCityInvalid,
    ClubDistrictInvalid,
    ClubNameInvalid,
    ClubPointInvalid,
    ClubSportsRequired,
)


def _typed_text(
    value: str, *, shortest: int, longest: int, refusal: type[Exception]
) -> str:
    """Text a desk typed: trimmed, runs of whitespace collapsed, then bounded.

    ``split()`` with no argument splits on any run of whitespace and drops the
    ends — the trim and the collapse in one step, as ``Name`` does it — so the
    bounds are on the text as it will be recorded.
    """

    collapsed = " ".join(value.split())
    if not shortest <= len(collapsed) <= longest:
        raise refusal()
    return collapsed


@dataclass(frozen=True, slots=True)
class ClubName:
    """What the club is called: trimmed, whitespace collapsed, 2–80 characters,
    and **never unique** — nothing checks that a club is who it says it is
    (``docs/adr/0182``, *Harder*)."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _typed_text(self.value, shortest=2, longest=80, refusal=ClubNameInvalid),
        )


@dataclass(frozen=True, slots=True)
class District:
    """The part of the city the club is in, as the desk writes it: free text,
    trimmed and collapsed, 2–64 characters. Searched, so it is folded beside the
    name in the projection."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _typed_text(
                self.value, shortest=2, longest=64, refusal=ClubDistrictInvalid
            ),
        )


@dataclass(frozen=True, slots=True)
class City:
    """The club's city, as the desk writes it: trimmed and collapsed, 2–64."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _typed_text(self.value, shortest=2, longest=64, refusal=ClubCityInvalid),
        )


@dataclass(frozen=True, slots=True)
class OfferedSports:
    """The sports a club offers: a **non-empty subset of the four**.

    They *filter* the ``Sport`` registry and never extend it (``docs/adr/0182``
    §1), so a club cannot declare a fifth sport or change how many play one.
    Held as a set — ticking a sport twice is ticking it — and read out in the
    registry's own order, never in the order the desk ticked them.
    """

    sports: frozenset[Sport]

    def __post_init__(self) -> None:
        if not self.sports:
            raise ClubSportsRequired()

    @classmethod
    def of(cls, sports: Iterable[Sport]) -> "OfferedSports":
        return cls(frozenset(Sport(sport) for sport in sports))

    def in_registry_order(self) -> tuple[Sport, ...]:
        return tuple(sport for sport in Sport if sport in self.sports)


@dataclass(frozen=True, slots=True)
class MapPoint:
    """Where the club is: **a precise point, stored as the desk dropped it.**

    A player's Location area is coarsened to a cell on the way in, because where
    a person plays is a fact about the person. A club is a public place and its
    point is printed on its door (``docs/adr/0182`` §6), so nothing here rounds.
    """

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not (
            math.isfinite(self.latitude)
            and math.isfinite(self.longitude)
            and -90.0 <= self.latitude <= 90.0
            and -180.0 <= self.longitude <= 180.0
        ):
            raise ClubPointInvalid()


@dataclass(frozen=True, slots=True)
class ClubDetails:
    """Everything the desk may change about its club, as one value.

    One value because the club website edits them on one page and a details
    change is one event carrying all five (``docs/adr/0182`` §5).
    """

    name: ClubName
    district: District
    city: City
    sports: OfferedSports
    point: MapPoint
