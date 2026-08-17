"""The snapshot input vocabulary both matchmaking engines read.

See ``docs/adr/0026-matchmaking-engines-snapshot-input-contract.md``.

**Snapshots, not aggregates.** An engine may not import a module, touch a
database, read configuration or call a clock, and the contexts that own this data
— Matches, Clubs, Courts — do not exist yet. So a calling module *assembles* the
facts an engine is given, and this file is the list of them. It is deliberately
the specification for what the Matches aggregate will have to own.

**The vocabulary is borrowed, never re-coined.** The ``Sport`` and its sold seat
count come from the kernel registry and are read from it here rather than carried
as a field, because *a sport's player count is never club-configurable* — a padel
match divides by four wherever it is read. Later slices add a seat's paid / held /
empty state, the match's phase, its court hold tier and its join cutoff, and those
are the clock and commitment rules' words spelled identically; renaming one here
would fork the clock.

**A Level is exact, and it is not an Uncertainty.** Both are branded over the
kernel's ``Ratio`` — an exact ``Fraction`` over two integers — and carried in
hundredths, the precision the rating context already publishes them at. The brands
are local to this vocabulary and the kernel is untouched: ADR-0022 records that
promoting ``Level`` and ``Sigma`` into the kernel is a *relocation* to be done when
a second engine needs them as vocabulary, and doing it here would mean moving the
rating engine's scale in the same commit as landing a forecast.

Exactness earns its keep one slice from now: a doubles team strength is a
``Ratio``-weighted blend of two Levels, so the strength of a team is exact and the
gap between two teams is exact, and the balance percentage derived from it does not
depend on the order two multiplications happened in. It stops being exact the
moment two Uncertainties are combined — quadrature leaves the rationals — and that
crossing has exactly one place, ``pairing/core.as_float``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NewType, final

from app.kernel import SPORT_SPECS, Ratio, Sport, invariant, ratio

#: The denominator a Level and an Uncertainty are carried over. Two decimals is
#: the precision the rating context publishes — ``band_for`` already rounds its
#: edges to two, because "Levels are carried to two decimals, so the edges are
#: too" — so a hundredth is the smallest difference that means anything.
HUNDREDTHS = 100

#: A player's Level (μ) on the rating scale, as an exact ratio.
Level = NewType("Level", Ratio)

#: A player's Uncertainty (σ), in the same units as a Level, as an exact ratio.
Uncertainty = NewType("Uncertainty", Ratio)

#: Who a player is, as far as an engine needs to know. An engine compares two of
#: these for equality — *is the current player in this seat* — and never parses,
#: orders or displays one, so the assembler is free to hand over whatever the
#: Matches context ends up using for a player identity.
PlayerRef = NewType("PlayerRef", str)


def _not_a_bool(value: int, named: str) -> int:
    """Refuse the one `int` that is never a rating.

    `bool` is a subclass of `int`, so `level(True)` typechecks and means a Level
    of 0,01 — a wrong answer rather than a loud one. The same guard as the money
    and time modules', because it is the same hole in the same place.
    """

    invariant(not isinstance(value, bool), f"{named} from a bool: {value!r}")
    return value


def level(hundredths: int) -> Level:
    """A Level in hundredths: 3,20 is ``level(320)``.

    Refused below one hundredth, because a Level of zero or less is not a point
    on any scale and every quantity derived from it — a team strength, a gap —
    would be quietly meaningless rather than loudly wrong.

    **The top of the scale is deliberately not checked here.** 1,0–5,0 lives in
    ``racketskill/core`` and ADR-0015 put it there *"so onboarding and the later
    match-update engine cannot develop two ideas of what σ means"*; a second copy
    of the bounds in this file would be exactly that. The pairing engine reads a
    Level as a value carried on the snapshot and never restates the scale, the
    confidence transform or its ceiling.
    """

    invariant(hundredths >= 1, f"level in hundredths: {hundredths}")
    return Level(ratio(_not_a_bool(hundredths, "level"), HUNDREDTHS))


def uncertainty(hundredths: int) -> Uncertainty:
    """An Uncertainty in hundredths: σ 0,84 is ``uncertainty(84)``.

    Zero is allowed and a Level of zero is not, which is the asymmetry between
    the two: *we are perfectly sure* is a limit case worth being able to express
    and worth being able to test against, while *this player is nowhere on the
    scale* is not a state.
    """

    return Uncertainty(ratio(_not_a_bool(hundredths, "uncertainty"), HUNDREDTHS))


@final
@dataclass(frozen=True)
class PlayerSkill:
    """What the platform believes about one player at one sport.

    A Level and an Uncertainty, never a Level alone — *"a rating is never only a
    number"*, and the whole reason the forecast reports a margin beside its
    estimate is that this pair arrives here intact.

    ``confidence`` is **carried, never computed with.** It is σ restated as a
    percentage for the player, and the transform that produces it and the ceiling
    it can never reach both belong to the rating context. The pairing engine
    passes it through for a caller that wants to show it and derives nothing from
    it, so retuning the transform cannot move a balance percentage.
    """

    player: PlayerRef
    level: Level
    uncertainty: Uncertainty
    confidence: int


@final
@dataclass(frozen=True)
class SeatSnapshot:
    """One seat of a match, and who is on it.

    ``occupant`` is absent when nobody is on the seat. The paid / held / empty
    distinction the roster rules turn on is the clock and commitment rules'
    vocabulary and lands with the roster slice that reads it; until then a seat
    is occupied or it is not.
    """

    occupant: PlayerSkill | None = None


@final
@dataclass(frozen=True)
class MatchSnapshot:
    """One match, as much of it as the matchmaking engines are given.

    ``current_player`` is the person the analysis is *for* — every matchmaking
    answer is relative to somebody, and *"a perfectly balanced match forty minutes
    away at twice your ceiling"* is a good match and a bad recommendation at the
    same time. They may or may not be seated; sides are oriented so that when they
    are, they come first.
    """

    sport: Sport
    seats: tuple[SeatSnapshot, ...]
    current_player: PlayerSkill

    def __post_init__(self) -> None:
        invariant(
            len(self.seats) == self.sold_seats,
            f"{self.sport.value} is sold in {self.sold_seats} seats, "
            f"snapshot carries {len(self.seats)}",
        )

    @property
    def sold_seats(self) -> int:
        """How many seats this match is sold in, from the kernel registry.

        Read rather than carried, so no snapshot can assert a two-player padel
        match into existence. *"A sport's player count is never club-configurable.
        No field on any club or court may override it; the value is read from
        exactly one place, everywhere."*
        """

        spec = invariant(
            SPORT_SPECS.get(self.sport), f"no spec for sport: {self.sport!r}"
        )
        return spec.players

    @property
    def occupants(self) -> tuple[PlayerSkill, ...]:
        """Everybody on a seat, in seat order."""

        return tuple(seat.occupant for seat in self.seats if seat.occupant is not None)
