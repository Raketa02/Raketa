"""What a forecast is, and the two strengths it is read from.

``v1/group`` owns the arithmetic; this holds the shapes it returns, because a
shape outlives a version. **One ``Forecast`` everywhere it appears** — the Games
card's figure, the proposer's ranking of a court and the booked game's screen
read the same type, so the caveat a provisional figure carries cannot fall off
on one of them.

**The σ of a four is combined outside this engine**, exactly as a pair's is.
``combine_sigma`` is RacketSkill's — *the single place any engine is allowed to
combine two standard deviations* — and ``.importlinter`` forbids one engine to
import the other, so a four's spread arrives through :class:`SigmaCombiner`,
handed in by the module that composes the two. Writing ``√(Σσ²)`` here would be
a second definition of an identity that already has an owner.

The group objective's shapes — the seated four, the three arrangements, ``G``,
its terms and its reason codes — went with the ranking (#580, PRD #569).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence, final, runtime_checkable

from app.engines.matchfit.core import ForecastAssumption
from app.kernel import invariant


@runtime_checkable
class SigmaCombiner(Protocol):
    """How several Uncertainties become one. **Supplied, never written here.**

    Independent uncertainties add in quadrature, and that rule has exactly one
    home — ``racketskill/core.combine_sigma``. A pair's combination already
    arrives through the module that composes the two engines; a four's arrives
    the same way, and this Protocol is the shape of that arrival rather than a
    second opinion about it.

    It is a function and not a number because the seating is on this side: an
    empty seat is read as its partner seated twice, so the σs a side is combined
    from are only known once the engine has filled it.
    """

    def __call__(self, sigmas: Sequence[float]) -> float: ...


@final
@dataclass(frozen=True, slots=True)
class Split:
    """The two side strengths a forecast was read from, and their difference.

    **The evidence behind the percentage.** ``pct`` says *how even*; this says
    *between what and what*, on the scale players already read levels on — which
    is ``docs/adr/0136``'s whole boundary: what crosses is an **input** to a
    figure already served, and never a second score.

    A side's strength is not the mean of the two people on it
    (``the-group-objective.md`` §3.1 — the weaker partner sets more of it), so
    these are numbers only the engine has: a client averaging seated levels would
    print a different pair, which is the arithmetic
    ``the-play-screens.md`` §11.3 refuses.

    **``gap`` is a property and signed.** A property, so there is no constructor
    that could take a difference its own two strengths do not make, and the card
    cannot print three numbers two of which subtract to the third. Signed,
    because the client's bar takes an *advantage* — your side's strength minus
    theirs — and an unsigned gap would leave it deciding which half is bigger,
    which is the same arithmetic in a smaller disguise.
    """

    #: The reader's own side — the first one handed to the forecast.
    your_side: float
    their_side: float

    @property
    def gap(self) -> float:
        """``your_side − their_side``. **Signed, and never re-derived.**"""

        return self.your_side - self.their_side

    @property
    def side_gap(self) -> float:
        """How far apart the sides are, however round. **What balance reads.**

        The forecast's own input, taken off the same two strengths the screen
        prints — so the percent and the split beside it cannot come from two
        subtractions.

        The codebase's own word, rather than a fresh one: *distance* already
        means kilometres here.
        """

        return abs(self.gap)


@final
@dataclass(frozen=True, slots=True)
class Forecast:
    """How even a game is forecast to be. **One type, everywhere it appears.**

    A full court's forecast and a provisional one — a side with a seat still
    empty — are one shape, because they are the same claim about different sets
    of people, and two shapes would be two places for the caveat to fall off.

    **``provisional`` is derived from the assumption rather than stored beside
    it.** The failure being guarded against is a screen showing the number
    without its caveat, and a sibling boolean is exactly how the two get
    separated in a refactor (``docs/adr/0108``). Here they cannot be: there is no
    way to construct a provisional forecast with nothing to say about what was
    assumed, and no way to state an assumption without the figure being marked.

    ``sigma_group`` crosses because **the confidence is part of the claim** — the
    evidence is named rather than a category — and it is combined outside this
    engine, like every other σ.
    """

    pct: int
    sigma_group: float
    #: What was assumed, or ``None`` when nothing was. One value today: a
    #: half-empty side is read as if the missing player matched the one already
    #: there.
    assumption: ForecastAssumption | None

    def __post_init__(self) -> None:
        invariant(0 <= self.pct <= 100, f"a forecast of {self.pct}%")
        invariant(self.sigma_group >= 0.0, f"a negative group σ: {self.sigma_group}")

    @property
    def provisional(self) -> bool:
        """Whether a seat was still empty when this was read.

        A property and not a field, so the number and its caveat are one value.
        """

        return self.assumption is not None


__all__ = ["Forecast", "SigmaCombiner", "Split"]
