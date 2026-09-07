"""What a challenge **is** right now, read off the seats and the clock.

**Derived, never stored** (#221). A status column would be wrong for the whole
gap between a deadline passing and a sweep noticing, and it would be the copy
that gets believed. So there is no status field on the aggregate, no status
column in the store, and this function is the only place a standing exists.

Five values, and they are the five this context can justify. The twenty card
states the prototype draws are a *presentation* vocabulary spanning money,
booking and results that nothing here owns; these are the ones the seats and the
clock can answer for.

*Challenge sent* and *Challenge for you* are **not** two standings. They are one
standing read from two sides, which is why nothing here takes a reader.
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable, final
from uuid import UUID

from app.kernel import Instant
from app.modules.challenges.domain.seats import Seat, SeatAnswer


@final
class Standing(str, Enum):
    """The five standings, as codes. A client's words are the client's own."""

    #: Somebody's answer is still owed and still wanted.
    AWAITING_ANSWERS = "AWAITING_ANSWERS"
    #: Every seat is accepted. **No event says this** — it is the fold's answer,
    #: and an event announcing it would be a second place for it to be true.
    ON = "ON"
    #: Nobody is waiting, somebody other than the organiser is in, and a seat is
    #: open. The state the builder is re-entered from — and **not a waiting
    #: room**: the people who are in are in, and a conversation between them has
    #: already started.
    LINE_UP_INCOMPLETE = "LINE_UP_INCOMPLETE"
    #: Over, and somebody said no.
    DECLINED = "DECLINED"
    #: Over, and nobody said anything.
    LAPSED = "LAPSED"


#: The two standings that mean *this challenge has ended*. An ended challenge is
#: not an **open challenge**, so the pair rule releases the moment it is reached
#: — with or without a sweep having run.
ENDED = frozenset({Standing.DECLINED, Standing.LAPSED})


def standing_of(seats: Iterable[Seat], *, organiser_id: UUID, now: Instant) -> Standing:
    """The challenge's standing, from its seats and this instant.

    The order of the questions is the design, and each rung is a decision:

    **Is anybody but the organiser still in it?** A challenge stands exactly as
    long as one is — accepted, or yet to answer. A decline reopens that one seat
    and disturbs nothing else, because the people who already agreed did nothing
    wrong and are already talking to each other; but when the last of them is
    gone, there is nobody left to keep faith with, and what stands is the
    organiser alone on an empty court, which is indistinguishable from never
    having sent. Singles gets the right answer for free.

    **Is an answer still owed?** *Awaiting* outranks *line-up incomplete*
    deliberately. A half-built padel court is not re-entered into the builder
    while somebody is still deciding — *a one-to-one padel challenge is half a
    game*, and it is the **acceptance** that produces `LINE_UP_INCOMPLETE`, not
    the empty seats it was sent with.

    **Is every seat accepted?** Then it is on, with no special case for the
    organiser and none for singles: their seat is accepted from birth, which is
    what makes *every seat accepted* the whole of the completion rule.
    """

    seats = tuple(seats)
    if not any(seat.is_live_at(now) and not seat.holds(organiser_id) for seat in seats):
        return _how_it_ended(seats)
    if any(seat.is_awaiting_at(now) for seat in seats):
        return Standing.AWAITING_ANSWERS
    if all(seat.is_accepted() for seat in seats):
        return Standing.ON
    return Standing.LINE_UP_INCOMPLETE


def _how_it_ended(seats: tuple[Seat, ...]) -> Standing:
    """Which of the two endings this was: somebody's no, or everybody's silence.

    **A no outranks silence, whatever order the two arrived in.** Somebody made a
    judgement about this challenge and silence is not one, so a challenge that
    was refused is a refused challenge; which clock happened to run out first is
    an accident of when each seat was invited, and a standing that turned on it
    would change meaning overnight without anybody doing anything.
    """

    if any(seat.answer is SeatAnswer.DECLINED for seat in seats):
        return Standing.DECLINED
    return Standing.LAPSED
