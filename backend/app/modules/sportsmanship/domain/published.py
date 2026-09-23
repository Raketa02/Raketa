"""What this context says out loud about a person — to everybody, them included.

**One answer off one window.** Every reader is shown an average out of five
beside how many different people it rests on, and since ``docs/adr/0179`` §5
that includes the person it is about: the coarse band that used to be the
subject's answer is retired, and the cost — an average beside a count is a
subtraction the subject can perform — is accepted by name in that record and
not re-argued here. What blunts it is everything below and beside this module:
the collapse, the window, no zero, no individual rating on any route, and the
matcher never reading it.

**The collapse is not here, and that is the point of the schema.** *Only a
rater's most recent stars about a person count* is
``sportsmanship_rating``'s primary key (``card_model.py``), so by the time rows
reach this module there is already exactly one per rater. What is left for
arithmetic is a mean and a rounding.

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

    **This reaches the person it is about, too** (``docs/adr/0179`` §5). The
    subject used to be answered with a coarse band off a separate method, so
    the figure had no path to them; the band is retired and the path is the
    one every reader takes.
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

    **Rounded once, here.** Nothing downstream divides again, and nothing
    downstream coarsens: the figure a subject reads is the figure a reader
    reads, to the digit.
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


__all__ = [
    "HIGHEST_AVERAGE",
    "LOWEST_AVERAGE",
    "RATER_WINDOW",
    "PublishedSportsmanship",
    "published_from",
]
