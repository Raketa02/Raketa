"""How long one invitee has to answer, and when their own day runs out.

**Dated per seat, when that seat was invited** (#221). Each person gets the whole
window, and a seat filled later starts its own: it cannot inherit a deadline from
a send it was not part of, which is what *only the newly seated are invited*
would otherwise quietly break.

**Forty-eight hours, and the rule that picks the number is stated**
(``docs/adr/0151``): **a window must exceed the gap between app opens, not equal
it.** Nothing in this repository reaches a phone its owner is not holding, so an
invitee finds out the next time they open the app — and a day, which is what
#217 adopted whole from the source documentation without an argument behind it,
*equals* the modal gap rather than clearing it. A window set to the length of the
thing it must outlast fails about half the time by construction: a seat invited
at seven on a Monday evening lapsed before a once-a-day player ever saw it, and
that player is the modal player of a sports app rather than an edge case. Two
days clear the gap by a whole one; three buy nothing the second did not and cost
a third day of the pair block.

**An admitted hypothesis, with its falsifier named** — ``ACCEPTANCE_GRACE``'s
discipline, and the reason this number is now argued rather than inherited:
**answer rate against time since invitation.** If answers cluster inside the
first day and the second adds nothing, the second day is not being used and the
number comes back down. The second reading is the **share of seats that lapse**,
which is the figure this window was moved to move.

**The lapse was still charged, and nothing here exempted an unseen invitation**
— an argument about the *answers challenges* strand, which stood down with #544
(the mechanics §15.4) and took its read, ``answering_for``, with it; kept as the
reason the window is what it is. A fourth shape was available — keep the day and
leave a seat nobody saw out of that read, as a withdrawn challenge already was.
It was refused: once the
window exceeds the gap between app opens, silence *is* the fact the strand exists
to measure, and somebody who opens the app less often than every other day
genuinely is slow to answer. The exemption would also need *did they see it*,
which is not a thing a server can observe — delivery is — and it breaks the
strand from the far side: unmeasurable if silence is filed as judgement has a
mirror in **unmeasurable if judgement is filed as absence.**

**Moving it moves nothing already sent.** A seat's ``answer_by`` is stamped when
that seat is invited and folded back off the stream (``seats.py``), so every
outstanding challenge keeps the promise it was sent with and no migration exists;
what a change moves is the promise made by the invitations that follow it. What
it *does* reach is the lapse sweep, which has only an event's timestamp to narrow
on — hence the second constant below.

It is spelled here rather than passed in — unlike ``interest.ttl_days``, which is
a released ruleset's and would be a second copy if this module held one. There is
no ruleset for this: the window is the promise the invitation makes, which is
behaviour a domain test can observe rather than configuration.

Nothing here reads a clock. The caller says when the seat was invited, exactly as
``window_of`` is handed what day it is.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Final

from app.kernel import Instant, instant

#: Two days from being asked. ADR-0151's number, and the only place it is written
#: — the send route derives its sentence from this rather than spelling it again.
ANSWER_WINDOW: Final = timedelta(hours=48)

#: Every window this log has ever stamped on a seat: this one, and each one that
#: stood before it. **Changing ``ANSWER_WINDOW`` means adding the old value
#: here** — appending, never replacing — and that is the whole maintenance this
#: ledger asks for. It is public so that a test can hold what this repository has
#: actually shipped; ``SHORTEST_WINDOW_EVER_STAMPED`` below is what a caller
#: narrowing on it wants, and no read should reach for this tuple directly.
#:
#: It exists because the lapse sweep cannot read a deadline. ``may_have_lapsed``
#: asks the store which challenges are old enough to hold a seat past its window,
#: and the only column it has to ask with is an event's ``occurred_at``: a seat's
#: own ``answer_by`` lives inside a serialized seat code, and a column that
#: answered it would be the derived standing, stored. So the read applies *a*
#: window to *historical* events, and the current one is the wrong choice —
#: today's forty-eight would be applied to seats stamped under yesterday's
#: twenty-four, which lapse a day before it looks for them.
WINDOWS_EVER_STAMPED: Final = (timedelta(hours=24), ANSWER_WINDOW)

#: The window as a whole number of hours, for the one description that has to
#: name it (``challenges/presentation/routes.py``) and the one seed refusal whose
#: whole subject is how stale a database may be (``seeds/screens.py``).
#:
#: **Here rather than at either call site.** *The only place it is written* stops
#: being true the moment a caller does the arithmetic itself, and two callers
#: doing it two different ways is how the sentence and the constant come apart
#: without anybody editing either.
ANSWER_WINDOW_HOURS: Final = int(ANSWER_WINDOW // timedelta(hours=1))

#: The window the lapse sweep narrows on. **The shortest one any live seat can
#: carry**, which is the only cutoff that is right whichever way the number next
#: moves: a seat stamped with a *longer* window is named early and costs a stream
#: read that appends nothing, and over-naming is free there — while a seat
#: stamped with a *shorter* one is named late, and a record written late is a
#: denominator that was wrong for as long as it took.
#:
#: A shortening is picked up here the moment ``ANSWER_WINDOW`` moves, because
#: ``min`` reads the new value; a lengthening is covered by the old value staying
#: in the ledger above.
SHORTEST_WINDOW_EVER_STAMPED: Final = min(WINDOWS_EVER_STAMPED)


def answer_by(invited_at: Instant) -> Instant:
    """When this seat's answer stops being wanted.

    Past it the seat reads as lapsed and the organiser may already have offered
    it to somebody else, so **a late answer is refused** rather than accepted
    late: an accept that resurrected the seat would be contradicting a card the
    platform has already drawn.
    """

    return instant(invited_at + ANSWER_WINDOW)
