"""What this context says out loud about a person — and what it says to them.

**Two answers off one window, and the second one deliberately cannot say the
first.** A reader is shown an average out of five beside how many different
people it rests on; the person it is about is shown a **coarse band and no
count**. That is not a rendering choice made at a screen — it is the rule
``docs/adr/0158`` is built around, and it lives here because a figure and a count
in front of the subject is a subtraction: an average moving from 4,80 over ten to
4,73 over eleven names the new rating as a 4, and they know who they played.
Every answer would be identifiable by the one person who must never see it, and
the failure mode is somebody being confronted about it at the club.

**The collapse is not here, and that is the point of the schema.** *Only a
rater's most recent stars about a person count* is
``sportsmanship_rating``'s primary key (``card_model.py``), so by the time rows
reach this module there is already exactly one per rater. What is left for
arithmetic is a mean, a rounding and three edges.

**The window is fifty people, not fifty ratings.** Read the other way round, a
weekly partner would eat twenty of the fifty slots and hand the farming problem
back through a side door after the key had just closed it at the front. The
constant is domain and never configuration: an environment that could widen it
would be an environment deciding how long an opinion follows somebody.

**Nothing is trimmed, at either end.** Trimming is the platform deciding which
raters were wrong, which is a larger claim than publishing the number — and there
is no appeal route behind either claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Sequence, final

from app.kernel import invariant

#: How many **people** a published figure rests on at most — the fifty most
#: recent raters, each contributing the one answer that stands.
#:
#: It is a count of raters and never of ratings, and the difference is the whole
#: reason there is a window at all: fifty *ratings* would let somebody's regular
#: partner occupy a fifth of them, which is what the collapse in the key exists
#: to prevent. Applied where the rows are read, and **checked** by the fold
#: below, so a caller that over-fetched cannot quietly publish a figure over a
#: wider record than this.
RATER_WINDOW: Final = 50

#: The bottom of the published scale, and the top. **Not re-derived from
#: ``card.py``'s star bounds** — those are what a person may tap, these are what
#: a mean of taps may be, and they are the same two numbers for one reason
#: rather than by construction. ``tests/unit/test_sportsmanship_published.py``
#: fails the build if the two stop agreeing.
LOWEST_AVERAGE: Final = 1.0
HIGHEST_AVERAGE: Final = 5.0

#: The two edges of the band the **subject** is shown. Whole stars, over a
#: one-to-five scale, which is the coarsest three-step reading that is still
#: about the scale a person taps.
#:
#: **They are coarse on purpose and the coarseness is the safety.** At one or two
#: ratings a band cannot be informative about any individual, and even at fifty a
#: step this wide moves for a change of habit rather than for one evening. What a
#: subject learns is *something is going wrong*, which is the useful half; who to
#: blame for it is the half that stops people answering honestly.
GOOD_FROM: Final = 4.0
MIXED_FROM: Final = 3.0


class SportsmanshipBand(StrEnum):
    """How somebody is coming across, in the three steps they may be told.

    **Three values and never a fourth for *nobody has said anything*.** A person
    nobody has rated has no band at all — the field is absent — on the rule this
    whole area applies to a fact nobody has measured: *we have not seen enough*
    and *they are bad at this* are different facts, and a value meaning the first
    is a value somebody eventually draws a colour for.
    """

    GOOD = "GOOD"
    MIXED = "MIXED"
    POOR = "POOR"


@final
@dataclass(frozen=True, slots=True)
class PublishedSportsmanship:
    """What other players said: the figure, and how many of them said it.

    **The two travel together and are never separable.** ``3,0 / 5 · 1 player``
    is visibly one person's opinion and reads as one, which is why this publishes
    from the very first rating with no minimum — the count is what makes that
    safe, and it is the same discipline the metered rows on the record take by
    printing their raw pairs beside their figures.

    **``raters`` is people and not ratings.** One row per rater is the store's
    shape, so the count of the window *is* the number of different people with an
    opinion — which is the number a reader actually wants and the one a weekly
    partner cannot inflate.

    **This never reaches the person it is about.** The subject is answered with
    :class:`SportsmanshipBand` instead, off a separate method on the port, so the
    figure has no path to them rather than a rule against taking it.
    """

    average: float
    raters: int

    def __post_init__(self) -> None:
        invariant(
            self.raters >= 1,
            "a figure over nobody is an absence, not a nought — the record omits "
            "the zone rather than publishing a verdict nobody gave",
        )
        invariant(
            self.raters <= RATER_WINDOW,
            f"a figure over more people than the window admits: {self.raters}",
        )
        invariant(
            LOWEST_AVERAGE <= self.average <= HIGHEST_AVERAGE,
            f"a mean of one-to-five stars that is not one of them: {self.average}",
        )


def published_from(stars: Sequence[int]) -> PublishedSportsmanship | None:
    """Fold one subject's window into the figure and the count. **Or nothing.**

    ``None`` for somebody nobody has rated, which is most people: the record
    omits the whole zone rather than drawing a nought, because nobody has been
    unpleasant who has never been on a court with anybody.

    **Halves round up, and the rule is spelled rather than borrowed.** ``round``
    rounds them to even, so 4,25 would print 4,2 and 4,35 would print 4,4 — a
    rule nobody reading a figure out of five expects, and one that would show two
    players a point apart on identical evidence. ``player_score`` makes the same
    argument for percentages in its own context; this is that argument at one
    decimal, and the two are separate because a context that imported the other's
    rounding would be importing the other's scale with it.

    **Rounded once, here.** The band below is coarsened from *this* number and
    never from the raw mean, so a subject's band cannot disagree at an edge with
    the figure a reader is shown.
    """

    window = tuple(stars)
    invariant(
        len(window) <= RATER_WINDOW,
        "a window wider than the rule allows reached the fold: "
        f"{len(window)} raters over a window of {RATER_WINDOW}",
    )
    if not window:
        return None
    return PublishedSportsmanship(
        average=int(10 * sum(window) / len(window) + 0.5) / 10,
        raters=len(window),
    )


def band_of(average: float) -> SportsmanshipBand:
    """Coarsen a published figure into the three steps its subject may be told.

    Takes the **published** figure rather than the rows, which is what keeps the
    two answers one record: there is one mean and one rounding on this platform,
    and this reads it rather than taking a second.
    """

    if average >= GOOD_FROM:
        return SportsmanshipBand.GOOD
    if average >= MIXED_FROM:
        return SportsmanshipBand.MIXED
    return SportsmanshipBand.POOR


__all__ = [
    "GOOD_FROM",
    "HIGHEST_AVERAGE",
    "LOWEST_AVERAGE",
    "MIXED_FROM",
    "RATER_WINDOW",
    "PublishedSportsmanship",
    "SportsmanshipBand",
    "band_of",
    "published_from",
]
