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
match divides by four wherever it is read. A seat's **paid / held / empty** state
is here now and is spelled exactly as the commitment rules spell it; the match's
phase, its court hold tier and its join cutoff land with the viability term that
reads them. Renaming any of those here would fork the clock.

**A Level is exact, and it is not an Uncertainty.** Both are branded over the
kernel's ``Ratio`` — an exact ``Fraction`` over two integers — and carried in
hundredths, the precision the rating context already publishes them at. The brands
are local to this vocabulary and the kernel is untouched: ADR-0022 records that
promoting ``Level`` and ``Sigma`` into the kernel is a *relocation* to be done when
a second engine needs them as vocabulary, and doing it here would mean moving the
rating engine's scale in the same commit as landing a forecast.

Exactness earns its keep on the doubles path: a team strength is a
``Ratio``-weighted blend of two Levels, so the strength of a team is exact and the
gap between two teams is exact, and the balance percentage derived from it does not
depend on the order two multiplications happened in. It stops being exact the
moment two Uncertainties are combined — quadrature leaves the rationals — and that
crossing has exactly one place, ``pairing/core.as_float``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import NewType, TypeAlias, final

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
class UnratedPlayer:
    """Somebody on a seat whom the platform has never rated **at this sport**.

    A player can be Established at tennis and unrated at padel, so this is a fact
    about a player at a sport rather than about a player, and it is an ordinary
    state rather than an error: somebody who onboarded for one sport and joined a
    match in another is in it.

    **Its own type, not a nullable Level on ``PlayerSkill``**, because *a rating
    is never only a number*: the Level, the Uncertainty and the Confidence arrive
    together or not at all. Three nullable fields with an all-or-nothing rule
    between them are three fields every reader has to defend against — the same
    argument ``results.py`` makes for two ``@final`` classes over one pair with
    two nullable ones.

    It carries a reference and nothing else, because a reference is all there is.
    An engine that wants a Level for this seat has to *say where it got one*.
    """

    player: PlayerRef


#: Somebody on a seat: either a rating, or a player the platform cannot place on
#: the scale at this sport. Both members are ``@final``, so the union is closed and
#: a third kind of occupant cannot be smuggled in by subclassing one of them — it
#: has to be added here, where every reader of the union can see it arrive.
Occupant: TypeAlias = PlayerSkill | UnratedPlayer


class SeatState(Enum):
    """A seat's commitment state. **Borrowed vocabulary, spelled verbatim.**

    Paid, held and empty are the commitment rules' three words and the shared
    glossary's, under **Roster**: *the paid seats, plus you if you could still
    join; a held seat contributes its player's level but not their attendance; an
    empty seat is imputed.* ADR-0026 requires the snapshot to spell them the same
    way, because renaming one here would fork the clock. This engine reads them;
    Matches will define them.

    **Paid and held are the same fact to the balance forecast, deliberately.**
    Both put a Level on a side. What separates them is whether the person will
    actually turn up, and that is the viability term's question — a match's
    likelihood of happening, not its evenness. Representing attendance risk as
    extra Uncertainty here would bury it inside a balance percentage, where it
    would be indistinguishable from not knowing how good somebody is and would
    make a held seat look like a worse *match* rather than a less certain one.
    """

    PAID = "paid"
    HELD = "held"
    EMPTY = "empty"


@final
@dataclass(frozen=True)
class SeatSnapshot:
    """One seat of a match: its commitment state, and who is on it.

    The two cannot disagree, and that is checked rather than trusted: an empty
    seat is exactly a seat with nobody on it. A seat carrying a state that
    contradicts its occupant is a caller's bug — an assembler that has lost track
    of a join — and every count downstream, the paid fraction viability reads
    included, would be quietly wrong rather than loudly.
    """

    state: SeatState = SeatState.EMPTY
    occupant: Occupant | None = None

    def __post_init__(self) -> None:
        invariant(
            (self.occupant is None) == (self.state is SeatState.EMPTY),
            f"a {self.state.value} seat carrying occupant {self.occupant!r}",
        )


@final
@dataclass(frozen=True)
class MatchSnapshot:
    """One match, as much of it as the matchmaking engines are given.

    ``current_player`` is the person the analysis is *for* — every matchmaking
    answer is relative to somebody, and *"a perfectly balanced match forty minutes
    away at twice your ceiling"* is a good match and a bad recommendation at the
    same time. They may or may not be seated; sides are oriented so that when they
    are, they come first. They are an ``Occupant`` and not a ``PlayerSkill``,
    because a player browsing padel matches may only ever have been rated at
    tennis, and refusing to analyse a match for them would hide every padel match
    from exactly the players most in need of one.
    """

    sport: Sport
    seats: tuple[SeatSnapshot, ...]
    current_player: Occupant

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
    def occupants(self) -> tuple[Occupant, ...]:
        """Everybody on a seat, in seat order — **paid and held alike.**

        The glossary's Roster is *the paid seats*, and a held seat *contributes
        its player's level but not their attendance*, so both are here: the two
        states differ in whether the person turns up, never in whether they count
        towards how even the match will be. Reading only the paid ones would drop
        a player who is in the match from the forecast of it.
        """

        return tuple(seat.occupant for seat in self.seats if seat.occupant is not None)

    @property
    def paid_seats(self) -> int:
        """How many seats are paid for, as distinct from merely held.

        Not read by the balance forecast, which cannot tell the two apart on
        purpose. It is here because the distinction has exactly one consumer —
        the viability term, which asks how likely the match is to happen — and
        because a snapshot that carried the state without ever counting it would
        be carrying a field nothing reads.
        """

        return sum(1 for seat in self.seats if seat.state is SeatState.PAID)
