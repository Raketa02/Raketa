"""The two passes that read across the whole screen: the repeat guard, then emphasis.

Everything above this module composes *one* region or *one* shelf and can be
right about it in isolation. These two cannot: whether a shelf is worth showing
depends on the shelf above it, and whether a card shouts depends on every other
card on the screen — which is ADR-0032's argument for order and ADR-0037's for
emphasis, made twice about the same object.

**They run in the order the specification names — repeat guard, then emphasis —
and today that order is not observable.** A dropped shelf is *entirely* repeats
of a shelf above it, so every card on it has a copy above; emphasis takes the
first in composed order, which is that copy. The two therefore commute, which is
recorded in `tests/unit/test_now_composition.py` rather than claimed as a
difference. The order stays because the equivalence belongs to the guard's **drop
condition** and not to the passes: a guard that ever dropped a shelf for partial
overlap, or for a ceiling on total rows, would let the flag land on a row nobody
sees — and a screen with nothing loud on it looks exactly like an ordinary
screen, so the failure would be silent.

**Neither pass composes anything.** Both take the screen and answer a screen,
narrowing before they compare and rebuilding only what they changed, so a card
they do not touch is the same object the composer produced.

**The guard cannot fire on today's screen, and that is stated rather than left
to be discovered.** The four lanes that ship are pairwise incapable of repeating
each other: shelf 1 holds matches with a free seat and shelf 2 holds full ones,
which is one exclusive rule apart, and shelves 4 and 5 hold people and clubs.
The shelf it is written for is `recentlyViewed` — reserved in the enum with no
producer (ADR-0085), no floor, and *48 hours, still joinable*, which is shelf 1's
own population filtered by a gesture. It arrives as a server change and not as an
app release, so it arrives without a chance to add the guard first.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Sequence
from uuid import UUID

from app.modules.now.domain.funnel import Scored
from app.modules.now.domain.screen import (
    Block,
    MatchCard,
    NowScreen,
    PersonCard,
    Shelf,
    ShelfCard,
)

#: The two numbers ADR-0037 gates emphasis on, beside *a seat is open*. The fit
#: floor is 90 because **4,3 %** of realistic scores reach it; the coverage floor
#: is 80 % because it removes exactly the measured thin population — one score in
#: twelve above 90 sits at 48 % coverage, an empty court with four of ten terms
#: excluded — and because a floor above 86 % could not fire at all while two
#: terms ship dark, and a guard that cannot fire is one nobody should watch.
#:
#: They are spelled here rather than in ``funnel.py`` because they are not the
#: funnel's: the funnel's floors decide what reaches a shelf, and these decide
#: what shouts once everything has. A shelf floor and an emphasis floor sharing a
#: home is how one comes to be tuned by somebody moving the other.
EMPHASIS_FIT_FLOOR = 90
EMPHASIS_COVERAGE_FLOOR = 80


def without_repeats(screen: NowScreen) -> NowScreen:
    """Drop a shelf whose every card is already on the shelf above it.

    **Entirely, and never partially.** A match is allowed on more than one
    shelf — *Best fit for you* and *New on Raketa* can honestly make two
    different claims about one match, and hiding a good match for having been
    mentioned is a worse screen than mentioning it twice. What the guard exists
    to stop is the shelf that adds nothing: six cards under a second title,
    which teaches a player that scrolling is not worth it.

    **The shelf above is the nearest one still standing**, not the one that
    happened to precede it in the composer's list. A dropped shelf is not on the
    screen, so comparing against it would be comparing against a row nobody
    scrolls past — and a shelf identical to a dropped one would then survive
    while the shelf it duplicates did not.

    **A door is stepped over rather than compared.** It has no cards, so it can
    neither repeat a shelf nor be repeated by one, and it is not a row that
    reads as a second helping of the row above. The question does not arise on
    today's screen — the door and the ranked pair are alternatives, so a door is
    always first — and stepping over it is the answer that stays right if it ever
    moves.

    **A shelf with no cards is kept.** It cannot be composed — an empty shelf is
    absent, which is the region/shelf asymmetry ADR-0070 turns on — and *every
    one of no cards is a repeat* is vacuously true, so a guard that did not say
    so would silently drop the one shape that should never have existed instead
    of leaving it visible.
    """

    kept: list[Block] = []
    above: frozenset[UUID] = frozenset()
    for block in screen.shelves.shelves:
        if not isinstance(block, Shelf):
            kept.append(block)
            continue
        mine = frozenset(_about(card) for card in block.cards)
        if mine and mine <= above:
            continue
        kept.append(block)
        above = mine

    if len(kept) == len(screen.shelves.shelves):
        return screen
    return replace(
        screen, shelves=replace(screen.shelves, shelves=tuple(kept))
    )


def emphasised(screen: NowScreen, *, scores: Sequence[Scored]) -> NowScreen:
    """Flag at most one card on the whole screen, or none at all.

    **The cap is the guarantee, not the thresholds.** Whatever the score
    distribution does as real data arrives, the screen's one loud colour cannot
    become wallpaper — which is what lets ADR-0037 keep the rule the whole screen
    rests on unamended: *coral is never decorative*.

    **The first in final composed order**, walking shelves in the server's order
    and cards in the shelf's. Nothing here re-ranks: the card that shouts is the
    first the player would reach, so *"why that one?"* has an answer she can see.

    **Any offer silences the screen entirely.** An offer is a seat with a clock
    on it at the very top of Now, and it is the loudest thing the product has to
    say; a suggestion shouting underneath it would be two things competing to be
    the one thing she does next.

    **Only a ranked card can shout, and that falls out of ``scores``.** The
    enrolled strip is not walked — she is already in those matches, so *take this
    seat now* is not a claim about them — and the arrival shelves carry people
    and clubs, which have no fit, no coverage and no seat. Neither needs a rule
    of its own: nothing on either has a score, and a card with no score cannot
    clear three gates.
    """

    if screen.offers.cards:
        return screen

    shouts = {one.match_id for one in scores if _shouts(one)}
    if not shouts:
        return screen

    blocks = list(screen.shelves.shelves)
    for position, block in enumerate(blocks):
        if not isinstance(block, Shelf):
            continue
        for seat, card in enumerate(block.cards):
            if not isinstance(card, MatchCard) or card.match_id not in shouts:
                continue
            cards = list(block.cards)
            cards[seat] = replace(card, emphasis=True)
            blocks[position] = replace(block, cards=tuple(cards))
            return replace(
                screen, shelves=replace(screen.shelves, shelves=tuple(blocks))
            )
    return screen


def _shouts(scored: Scored) -> bool:
    """ADR-0037's three gates, evaluated together and never two of the three."""

    return (
        scored.fit >= EMPHASIS_FIT_FLOOR
        and scored.coverage >= EMPHASIS_COVERAGE_FLOOR
        and scored.has_free_seat
    )


def _about(card: ShelfCard) -> UUID:
    """The thing a card is about, which is what identifies it.

    Never its position and never the shelf it sits in: one match may appear on
    two shelves and it is the same match, which is the only reading under which
    *this shelf repeats the one above* means anything.
    """

    if isinstance(card, MatchCard):
        return card.match_id
    if isinstance(card, PersonCard):
        return card.player_id
    return card.club_id
