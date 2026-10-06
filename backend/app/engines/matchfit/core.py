"""The Match Fit vocabulary — what outlives a version and a ruleset.

``racketskill/core`` holds the scale, the bands and the σ rule for the same
reason this module exists: a name two rulesets disagree about is a name that has
stopped meaning anything. A ruleset *names* these; a version *computes* with
them; neither may add one.

**Three names are left, because three are read.** The "who fits whom" ranking
went (#580, PRD #569) and took its terms, evidence kinds, liveness signals,
modifiers, tag relationships and group terms with it: nothing the new games call
scores a person against another. What stays is the kind of game, the six
strands a Player Score is read in, and the one assumption a provisional forecast
makes.
"""

from __future__ import annotations

from enum import Enum


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


class ReliabilityStrand(str, Enum):
    """The six strands a reliability reading is built from, read separately.

    The published Player Score blends them at 35/20/15/12/10/8 and the player
    record prints each (``docs/adr/0140``). The two per-mode blends the ranking
    weighed them by went with it (#580), so the published one is the only blend
    left.

    **The sixth name is not the one that was struck, and the difference is the
    whole of ``docs/adr/0160``.** *Confirms results* asked whether a game reached
    an agreed score, which is a fact about a **pair**, and every denominator
    tried on it docked somebody ADR-0049 protects — both sides of an honest
    disagreement included (``docs/adr/0137``). *Answers about results* asks
    whether **this person** replied to a score put in front of them, and a
    counter is as good an answer as an acceptance, so disagreeing costs nothing
    and only silence is priced.
    """

    SHOWS_UP = "SHOWS_UP"
    ANSWERS_CHALLENGES = "ANSWERS_CHALLENGES"
    ANSWERS_RESULTS = "ANSWERS_RESULTS"
    KEEPS_PLANS = "KEEPS_PLANS"
    SETTLES_UP = "SETTLES_UP"
    SPORTSMANSHIP = "SPORTSMANSHIP"


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
