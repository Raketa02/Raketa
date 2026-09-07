"""How long one invitee has to answer, and when their own day runs out.

**Dated per seat, when that seat was invited** (#221). Each person gets a day,
and a seat filled later starts its own: it cannot inherit a deadline from a send
it was not part of, which is what *only the newly seated are invited* would
otherwise quietly break.

**Twenty-four hours, and it is a product decision rather than a tuned number.**
It is spelled here rather than passed in — unlike ``interest.ttl_days``, which is
a released ruleset's and would be a second copy if this module held one. There is
no ruleset for this: the day is the promise the invitation makes, and moving it
moves what every outstanding challenge already said.

Nothing here reads a clock. The caller says when the seat was invited, exactly as
``window_of`` is handed what day it is.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Final

from app.kernel import Instant, instant

#: One day from being asked. AC-140's number, and the only place it is written.
ANSWER_WINDOW: Final = timedelta(hours=24)


def answer_by(invited_at: Instant) -> Instant:
    """When this seat's answer stops being wanted.

    Past it the seat reads as lapsed and the organiser may already have offered
    it to somebody else, so **a late answer is refused** rather than accepted
    late: an accept that resurrected the seat would be contradicting a card the
    platform has already drawn.
    """

    return instant(invited_at + ANSWER_WINDOW)
