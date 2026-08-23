"""What the platform fixes about a court, in the words two contexts read verbatim.

Today that is one fact: **whether there is a roof**. Clubs authors it —
``CourtCategory.cover``, required at construction — and Now renders it on the
spine of every match card, which is where ADR-0073 put it and why:

    it behaves like place, not like state, and leaving it on six situations
    fails the player at the exact moment they are choosing.

**It lives in the kernel because a second implementation of it would be a
defect** — ADR-0022's own test, and the same answer ``causes.py`` got. A closed
two-value set declared once in Clubs and once in Now is a mapper between two
spellings of one fact, and the mapper is the thing that goes wrong.

**Not in ``sports.py``.** A roof is a property of the place the game is played
in, not of the game, and a squash court is indoors because of the building
rather than because of the sport. Filing it under the registry would make the
next reader look for a venue fact among the seat counts.
"""

from __future__ import annotations

from enum import Enum

from app.kernel.invariants import invariant


class Cover(str, Enum):
    """Indoor or outdoor, as a fact about *where* rather than about state.

    ADR-0073 moved it onto the spine of every card: it behaves like place, not
    like state, and leaving it on six situations failed the player at the exact
    moment they were choosing — in November in Kraków it is the most important
    fact about a padel court, and it was absent from every shelf.

    **Two values in v1, and a roof is ``INDOOR``** (ADR-0090). *Covered but
    open-sided* is a real padel configuration and reads as neither; the question
    the card answers is *will I be rained on*, and a canopy answers that the way
    a wall does. What it does not answer is *will I be cold*, which is the loss
    this takes knowingly — a third value is an additive member here **and a
    client release for its copy**, and no document in the specification set has
    asked for one.
    """

    INDOOR = "indoor"
    OUTDOOR = "outdoor"


#: Pinned rather than counted, so a third value is a decision somebody made in a
#: diff — the rule ``CAUSE_COUNT`` and ``OUTCOME_COUNT`` already hold. It is
#: worth more here than in most places: a member arriving is a client release,
#: because each client holds an exhaustive table over these names.
COVER_COUNT = 2

invariant(
    len(Cover) == COVER_COUNT,
    f"the enumeration names {len(Cover)} covers, not {COVER_COUNT}",
)
