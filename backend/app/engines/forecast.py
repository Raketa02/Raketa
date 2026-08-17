"""The ``BalanceForecastEngine`` Protocol and the vocabulary it speaks.

A consuming context depends on this abstraction, never on a version, so swapping
``pairing/v1`` for a later lineage — or for an implementation behind HTTP — is a
wiring change at the FastAPI boundary like any other port (``docs/adr/0015``).

**One analysis object.** The engine returns a ``PairingAnalysis`` rather than a
bare forecast, because a caller that needs the forecast almost always needs the
seat target, the target band and the ranked splits too, and the four have to agree
with each other (``docs/adr/0026``). Later slices fill the fields this one does
not; the object is the shape from the start so lighting them up is a constant
change and not a signature change.

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

from app.engines.matchmaking import Level, MatchSnapshot
from app.kernel import Instant, Result


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
class PairingAnalysis:
    """Everything the pairing engine concluded about one match, together.

    ``engine_version`` travels on the result because every constant in the engine
    is an admitted hypothesis with a measurement that would falsify it, and you
    cannot falsify one you cannot attribute an answer back to. A Match Fit score
    carries this one *and* its own, since it has two producers.
    """

    forecast: Result[BalanceForecast, NoForecast]
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
