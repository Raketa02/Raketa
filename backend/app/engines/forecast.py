"""The ``BalanceForecastEngine`` Protocol and the vocabulary it speaks.

A consuming context depends on this abstraction, never on a version, so swapping
``pairing/v1`` for a later lineage — or for an implementation behind HTTP — is a
wiring change at the FastAPI boundary like any other port (``docs/adr/0015``).

**One analysis object.** The engine returns a ``PairingAnalysis`` rather than a
bare forecast, because a caller that needs the forecast almost always needs the
seat target, the target band and the ranked splits too, and the four have to agree
with each other (``docs/adr/0026``). All four are now carried; what a later slice
still changes is *when* the forecast can answer, not the shape of the object.

**A forming match answers what it can.** The four fields decline independently,
because they need different things: a forecast needs every seat filled, a seat
target needs the match to be exactly one seat from full, a band needs one seated
player. So a padel court with three players advertises the Level its last seat is
aimed at while honestly having no forecast at all, and every decline is a
``Result`` carrying a machine code and a payload rather than a silence a caller
has to interpret.

**The chosen split and the forecast are one object, not two.** A card showing
*you and Bo against Cy and Dee, 84% balanced* is showing one conclusion twice,
and the two could disagree only if a caller could pair a forecast with a
different arrangement than the one it was computed from. It cannot: the winning
``Split`` carries the forecast that ranked it, and ``PairingAnalysis.forecast``
is that same object.

**Numbers and machine codes, never words.** The engine emits no display text, no
formatted Level and no formatted percentage. ``estimate`` is a whole percent and
``favourite_share`` a whole percent; how they are drawn, and in which language,
is the client's, and the two clients do not share a shape.

**The estimate ranks; the card decides whether to print it.** ``certainty`` grades
the margin and ``fit_to_print`` reads that grade, but a forecast too uncertain to
show is still the best guess available — suppression is presentation, and Match
Fit's balance term reads the point estimate either way. Withholding it from the
ranking would make an uncertain match unrankable rather than honest.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Protocol, TypeAlias, final, runtime_checkable

from app.engines.matchmaking import Level, MatchSnapshot, PlayerRef
from app.kernel import Instant, Ratio, Result


class Certainty(Enum):
    """The forecast's grade of its own margin.

    A statement about the platform's knowledge and never about the players: two
    matches can both be forecast at 78% balanced, one between players it has
    watched for a season and one between two people who answered a questionnaire
    yesterday, and they are not the same claim.
    """

    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


@final
@dataclass(frozen=True)
class SidesNotFormed:
    """No two sides can be made of this roster, so there is nothing to forecast.

    Returned rather than raised: asking for a forecast of a match nobody has
    joined is a perfectly reasonable question and the honest answer is *there is
    no roster here*, which a card renders as saying nothing rather than as a
    number (``docs/adr/0022``). A caller branches; nothing catches.

    Payload, not prose (``Reason``): the sport and how many people were actually
    on a seat, which is what a client needs to say whichever thing it wants to
    say.
    """

    sport: str
    seated: int
    sold: int
    kind: Literal["sides_not_formed"] = "sides_not_formed"


#: Every reason the pairing engine can give for having no forecast.
NoForecast: TypeAlias = SidesNotFormed


@final
@dataclass(frozen=True)
class SeatUnderDetermined:
    """More than one seat is open, so *which Level is this seat aimed at* has no
    answer — and none is invented.

    With two seats open there are two Levels to choose and one equation between
    them: every Level in a wide interval is the right answer for the last seat
    given *some* answer for the other one. Naming one of them would be reporting
    a preference as a calculation. A match in that state advertises its
    ``TargetBand`` instead, which is a claim the roster actually supports.

    Zero seats open reaches the same reason for the opposite cause: a full match
    has no seat to aim.
    """

    sport: str
    open_seats: int
    sold: int
    kind: Literal["seat_under_determined"] = "seat_under_determined"


@final
@dataclass(frozen=True)
class NobodySeated:
    """Nobody is on a seat, so the match is aimed at nothing yet.

    A target band is the mean of the seated Levels, and the mean of no Levels is
    not a wide band — it is no band. One seated player is enough and is the whole
    requirement; this is the single case that cannot answer.
    """

    sport: str
    sold: int
    kind: Literal["nobody_seated"] = "nobody_seated"


#: Every reason there is no seat target. ``SidesNotFormed`` is here because a
#: doubles seat target is solved *through* the pairing: an arity this version has
#: no pairing rule for has no sides to even up, so it has no seat to aim either,
#: and that is the same fact rather than a second one.
NoSeatTarget: TypeAlias = SeatUnderDetermined | SidesNotFormed

#: Every reason there is no target band.
NoTargetBand: TypeAlias = NobodySeated


@final
@dataclass(frozen=True)
class TargetBand:
    """The Level range a forming match is aimed at. **Blunt by design.**

    Carried as a midpoint and a half width rather than as two edges, so the three
    numbers cannot disagree: the midpoint is what the roster actually says — the
    mean of the seated Levels — and the width is one constant applied to it.
    ``low`` and ``high`` are properties for the same reason ``fit_to_print`` is.

    **Not clamped to the rating scale.** 1,0–5,0 belongs to the rating context and
    this engine does not restate it, exactly as ``level()`` declines to; a caller
    drawing the band against a scale it owns is the one place that clamp means
    anything. So a band around a Level near the bottom of the scale can reach
    below it, and that is a true statement about a match, not a Level being
    claimed about a player.
    """

    midpoint: Level
    half_width: Ratio

    @property
    def low(self) -> Level:
        return Level(Ratio(self.midpoint - self.half_width))

    @property
    def high(self) -> Level:
        return Level(Ratio(self.midpoint + self.half_width))


@final
@dataclass(frozen=True)
class BalanceForecast:
    """How even a match is predicted to be — an estimate, and a margin.

    ``estimate`` is the balance percentage: 100 is dead even. ``margin`` is how
    wrong that number could be, **in the same units**, which is what makes
    *"49/51"* and *"49/51, and we barely know these people"* different claims.

    ``favourite_share`` and ``underdog_share`` are the split bar, and the bar is a
    *rendering* of the percentage rather than a second opinion about it: the
    underdog's share is half the estimate, so the two saturate at the same instant
    and cannot disagree in the gap between them. The bar says how lopsided, not
    who — **which side is ahead is read off the two strengths**, because under a
    wide Uncertainty the magnitude of a gap is knowable when its direction is not,
    and a bar that named a favourite there would be inventing one.

    ``beyond_scale`` distinguishes *this is a mismatch* from *this is the lowest
    number the scale prints*. Both show the floor; only one of them means the
    scale ran out.
    """

    estimate: int
    margin: int
    certainty: Certainty
    favourite_share: int
    underdog_share: int
    beyond_scale: bool
    side_a: Level
    side_b: Level
    expected_gap: float

    @property
    def fit_to_print(self) -> bool:
        """Whether the margin is narrow enough for the estimate to be shown.

        A property and not a field, so it cannot drift from the grade it is read
        from. Presentation only — the estimate ranks either way.
        """

        return self.certainty is not Certainty.LOW


@final
@dataclass(frozen=True)
class Split:
    """One of the ways a four-player roster divides into two teams.

    **Not the split bar.** That is ``favourite_share`` / ``underdog_share`` on the
    forecast, and it says how lopsided a match is. A ``Split`` says *who is with
    whom*, and the domain word for it is the glossary's: *four players admit
    exactly three splits, and the engine searches all three.*

    ``side_a`` and ``side_b`` are the two teams as player references, oriented so
    the current player's team is ``side_a``. The strengths of those same two
    teams, in the same order, are ``forecast.side_a`` and ``forecast.side_b`` —
    membership and strength are built together and cannot be paired up wrongly by
    a caller.

    All three are returned ranked, not only the winner, because
    ([ADR-0025](../../docs/adr/0025-binding-pairing-for-counted-matches.md)) the
    roster of a counted match may elect a different one up to commitment, and an
    election needs the arrangement it is electing.
    """

    side_a: tuple[PlayerRef, ...]
    side_b: tuple[PlayerRef, ...]
    forecast: BalanceForecast


@final
@dataclass(frozen=True)
class PairingAnalysis:
    """Everything the pairing engine concluded about one match, together.

    ``forecast`` is the *chosen* split's forecast in doubles and the only one
    there is in singles, so a caller that wants one number never has to know
    which sport it is looking at. ``splits`` is empty for a two-player sport —
    singles has no pairing, and an empty tuple is how that is said rather than a
    one-element list implying an election nobody can make.

    ``seat_target`` and ``target_band`` are what a match says about the seats it
    has *not* filled, and they are two answers to one question at two
    resolutions. The seat target is exact and needs the match to be one seat from
    full; the band is blunt and needs one seated player. **The band is the
    fallback whenever the seat target declines**, so a caller never has nothing to
    say about a forming match, and the two are carried together precisely so that
    falling back is a branch on a value rather than a second call.

    The three answers are computed from one snapshot in one pass, which is the
    whole reason they are one object: a card showing *this seat is aimed at 2,71*
    beside a forecast drawn from a different roster would be two readings of a
    match that only has one.

    ``engine_version`` travels on the result because every constant in the engine
    is an admitted hypothesis with a measurement that would falsify it, and you
    cannot falsify one you cannot attribute an answer back to. A Match Fit score
    carries this one *and* its own, since it has two producers.
    """

    forecast: Result[BalanceForecast, NoForecast]
    splits: tuple[Split, ...]
    seat_target: Result[Level, NoSeatTarget]
    target_band: Result[TargetBand, NoTargetBand]
    engine_version: str


@runtime_checkable
class BalanceForecastEngine(Protocol):
    """A pure, versioned balance-forecast engine.

    ``analyse`` is a function of the snapshot and the instant it is asked at, and
    nothing else: no clock, no randomness, no state between calls. ``now`` is
    explicit and rounded to the minute, which is what makes a score reproducible
    from its stored inputs and cacheable for a minute rather than never.
    """

    @property
    def version(self) -> str: ...

    def analyse(self, *, snapshot: MatchSnapshot, now: Instant) -> PairingAnalysis: ...
