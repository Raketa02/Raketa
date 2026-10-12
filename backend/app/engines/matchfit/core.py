"""The Match Fit vocabulary — what outlives a version and a ruleset.

``racketskill/core`` holds the scale, the bands and the σ rule for the same
reason this module exists: a name two rulesets disagree about is a name that has
stopped meaning anything. A ruleset *names* these; a version *computes* with
them; neither may add one.

**Three vocabularies are left, because three are read.** The "who fits whom"
ranking went (#580, PRD #569) and took its terms, evidence kinds, liveness
signals, modifiers, tag relationships and group terms with it: nothing the new
games call scores a person against another. What stays is the kind of game, the
four bands Player reliability is read in (with where each begins), and the one
assumption a provisional forecast makes. The six strands a Player Score was read
in left with the strands themselves (#659; ``docs/adr/0195`` §1).
"""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Final, Mapping


class SearchMode(str, Enum):
    """What kind of game this is. **Two values, never three.**

    ``PlayIntent`` is a player's declaration and has three values; this is the
    *game's* kind — a Games card is competitive or for fun — and has two. The
    arities differ on purpose, so the likeliest bug in reading one as the other
    is a type error rather than a paragraph in a document.

    It picks the level window's tolerance (``matchmaking/domain/level_window.py``)
    and nothing else here.
    """

    COMPETITIVE = "COMPETITIVE"
    FOR_FUN = "FOR_FUN"


class ReliabilityBand(str, Enum):
    """The word under a player's reliability figure (``docs/adr/0195`` §1).
    **Four bands, served by the backend**: a client draws the word from the band
    and holds no threshold of its own.

    **Here, and never in a context**, for the reason ``racketskill/core`` holds
    the Level's bands: it is a closed vocabulary read by every surface that
    shows the figure — a player's record, a group's Members list — and by the
    one thing that acts on it, the reliability filter in the pair rule (#661).
    A copy in each would satisfy every test in its own context while being free
    to drift, and a client would be handed two words for one band.

    The words the phone draws — *Very high*, *High*, *Medium*, *Low* — are its
    own; the retired tone ladder's *Reliable*, *Holding* and *Under the bar*
    named a bar at 70 that nothing applies.
    """

    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


#: Where each band begins, in points out of a hundred — **the one home of these
#: three numbers** (``docs/adr/0195`` §1): Very high 90–100, High 75–89, Medium
#: 50–74, Low below 50. The filter's *the figure that brings you back* is a
#: floor read from here (#661), so the sheet and the filter cannot disagree
#: about where High starts. Highest first: ``reliability_band_of`` walks it.
RELIABILITY_BAND_FLOORS: Final[Mapping[ReliabilityBand, int]] = MappingProxyType(
    {
        ReliabilityBand.VERY_HIGH: 90,
        ReliabilityBand.HIGH: 75,
        ReliabilityBand.MEDIUM: 50,
        ReliabilityBand.LOW: 0,
    }
)


def reliability_band_of(points: int) -> ReliabilityBand:
    """The band a figure of ``points`` falls in — the highest whose floor it
    reaches. A figure is clamped to 0–100 before it gets here, so ``LOW``'s
    floor of nought catches everything below fifty."""

    for band, floor in RELIABILITY_BAND_FLOORS.items():
        if points >= floor:
            return band
    return ReliabilityBand.LOW


class ForecastAssumption(str, Enum):
    """What a **provisional** forecast assumed, as a code the client renders.

    One value, because there is one assumption: a side with a seat still empty is
    read **as if the missing player matched the one already there**. It is an
    enum rather than a bare string for the reason every other vocabulary here is
    one — an assumption the client cannot name is a caveat it cannot print, and a
    provisional number rendered without its caveat is the failure the whole
    shape exists to prevent (``docs/adr/0108``).

    A second value would be a second thing the product is willing to assume about
    somebody who is not there, and that is a decision rather than a constant.
    """

    EMPTY_SEAT_MATCHES_ITS_PARTNER = "EMPTY_SEAT_MATCHES_ITS_PARTNER"
