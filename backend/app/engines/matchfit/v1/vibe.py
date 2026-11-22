"""A For-fun table's **Social vibe** — how much of what everyone at it carries
is shared there (``docs/adr/0207`` §2, #830).

It reads as one sentence: *on average, each tag at this table is carried by that
share of the other players*. With ``n`` people at the table, ``Tᵢ`` the tags
player ``i`` carries and ``c_t`` how many of them carry tag ``t``::

    social_vibe = round_half_up( 100 × Σᵢ Σ_{t∈Tᵢ} (c_t − 1)/(n − 1)  ÷  Σᵢ |Tᵢ| )

**Every surface that draws it is to call this one function**, so no two of
them can disagree (``docs/adr/0207`` §11). The group deck's cards do since
#830, and the proposer's For-fun building since #831, through the exact
share; a game's details, the booked game, the Friends card and Post a game's
fits follow in #833–#835.

**What crosses in is the tags that count, and only identical tags are shared.**
A tag is compared for equality and nothing else, so no tag weighs more than
another and related ones earn no credit for each other. Which tags don't count
(*Open to meet someone*) is the Player profile's to say, beside its vocabulary,
and they are removed before the engine is asked: the engine holds no list of
tags, because it holds no vocabulary.

**No constants and no ruleset.** The percent and the half are the formula's
own; the bands a number is worded in are the app's.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Hashable, Sequence, Set
from fractions import Fraction
from math import floor

#: A whole percent is a hundredth, and half of one rounds up.
_PERCENT = 100
_HALF = Fraction(1, 2)


def social_vibe_share(table: Sequence[Set[Hashable]]) -> Fraction | None:
    """The Social vibe, **exact**: the share of the table's carryings that the
    other players carry too, averaged over every carrying.

    For a caller that compares two tables before anything is printed — the
    proposer ranks fours by it unrounded (``docs/adr/0207`` §1) — and the one
    place :func:`social_vibe` rounds from. A :class:`~fractions.Fraction`,
    because a table's share is a ratio of small whole numbers and a float would
    round a half the wrong way.

    ``table`` is one set of counted tags per person at the table, an empty one
    for somebody who carries none — they share nothing, and they are still one
    of the others each tag could be carried by. **``None`` with fewer than two
    people**, where there is nobody to share with; and **``None`` when nobody
    carries a tag**, which is nothing to measure rather than a table that shares
    nothing. At a real table that never happens: everybody holds a counted tag.
    """

    people = len(table)
    if people < 2:
        return None
    carried = sum(len(tags) for tags in table)
    if carried == 0:
        return None
    carriers = Counter(tag for tags in table for tag in tags)
    shared = sum(
        (Fraction(carriers[tag] - 1, people - 1) for tags in table for tag in tags),
        Fraction(0),
    )
    return shared / carried


def social_vibe(table: Sequence[Set[Hashable]]) -> int | None:
    """The Social vibe as the whole percent a card prints — **rounded half up**,
    ``floor(100·x + ½)``, as the Vibe % is. ``None`` where
    :func:`social_vibe_share` has no value, and nothing is drawn.

    In singles it is the plain overlap of the two: twice the tags they share,
    over every tag the two carry.
    """

    share = social_vibe_share(table)
    if share is None:
        return None
    return floor(_PERCENT * share + _HALF)


__all__ = ["social_vibe", "social_vibe_share"]
