"""When a card may be answered: **the day after, and for a week.**

Two clocks, and neither of them is configuration. They are what a player is
promised about being asked — *not tonight*, and *not for ever* — which is
behaviour a domain test can observe, and an environment that could select one
could select a rule that is true on a laptop and false in production. It is the
posture ``games/domain/windows.py`` takes for its own three, and this context
takes it for the same reason.

**Both edges run from ``games``' ``played_at``**, which is *the moment somebody
said we played* and not the hour four people stood on a court. It is therefore
never earlier than the game itself, so *not until the day after it was played* is
satisfied conservatively: an entry three days late moves the card three days
later, never earlier. **A full court nobody recorded runs from its booked hour**
(#655): nobody said when, so the hour is the only moment the evening has, and
its card is drawn from when its entry window closes — an hour into the day the
card is open — until a week after the day after.

A window anchored instead to the moment a *score* settled would restart
somebody's week every time two people argued about it for another day, and would
make the card's life a property of the argument rather than of the evening.
Settlement is a separate gate and it is the port's: a game still being argued over
is not offered at all, and if it settles inside the week its card appears then and
still closes on the evening's own clock.

**The cost of that is named rather than discovered.** In the ordinary path a lone
score confirms itself when its window closes, exactly as the card opens, and the
card gets its full seven days. Where two sides put scores up and neither gave way,
settlement can land as much as a day into the week — so that card is drawn for six
days rather than seven. One day, on the games where somebody argued, is the price
of a card whose life is a property of the evening and not of the argument.

**Open is inclusive, closed is exclusive.** Written the other way round, the
first edge asks somebody how it went in the ten minutes after losing 6-2 6-1 and
the second leaves a dead card in the list for an eighth day.

**Nothing here reads a clock.** The caller says what instant it is, exactly as
every window in ``games`` is handed one.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Final

from app.kernel import Instant, instant

#: How long after the game the card appears. **A day**, because an answer given
#: in the ten minutes after a bad loss is not the answer this context is for.
#: It is the same day this platform already asks of somebody it needs an answer
#: from, and it is kept as its own constant rather than folded into *eight days*
#: below, because gluing the two would hide both arguments.
CARD_OPENS_AFTER: Final = timedelta(days=1)

#: How long the card then stays. **A week**, and then it is gone — ignoring it
#: costs nothing, so the only thing an unanswered card can do is accumulate, and
#: a list of chores nobody is obliged to do is a list nobody reads.
CARD_STAYS_OPEN_FOR: Final = timedelta(days=7)


def card_opens_at(played_at: Instant) -> Instant:
    """The first moment this player may be asked how that evening went."""

    return instant(played_at + CARD_OPENS_AFTER)


def card_closes_at(played_at: Instant) -> Instant:
    """The moment the card is gone, whether or not anybody answered it.

    Nothing sweeps it and nothing records that it lapsed: *not rating produces
    no strand, no penalty and no record of the omission*, so the expiry is a
    fold over the evening's own clock and there is nothing for a job to correct.
    """

    return instant(card_opens_at(played_at) + CARD_STAYS_OPEN_FOR)


def card_is_open(*, played_at: Instant, now: Instant) -> bool:
    """Whether the card for a game played then may be drawn at this instant."""

    return card_opens_at(played_at) <= now < card_closes_at(played_at)


__all__ = [
    "CARD_OPENS_AFTER",
    "CARD_STAYS_OPEN_FOR",
    "card_closes_at",
    "card_is_open",
    "card_opens_at",
]
