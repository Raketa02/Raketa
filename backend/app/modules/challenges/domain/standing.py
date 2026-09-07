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


#: The two standings that mean *this challenge has ended* — there is nothing
#: left to arrange and nothing left to do. Read by ``Challenge.invite``, which
#: refuses to seat anybody into one; by the standing the client prints; and by
#: the **mutual mint**, which asks *does a challenge already stand between these
#: two* and would open a second game on a repeat tap without it.
#:
#: **``ON`` is not here, and adding it would be the wrong way to release a pair.**
#: A challenge every seat accepted is not over: it produced a game, which is the
#: opposite of nothing being left. See :data:`ARRANGING`.
ENDED = frozenset({Standing.DECLINED, Standing.LAPSED})

#: The standings that mean *these two are still arranging a game*, and **this is
#: the set the one-open-challenge-per-pair rule reads** — not the complement of
#: :data:`ENDED` (``docs/adr/0142`` §1, on
#: [#343](https://github.com/Raketa02/Raketa/issues/343)).
#:
#: The pair rule asks its own question, and it is neither *has this ended* nor
#: *is this alive*: it is **are these two still arranging a game?** Held while
#: an answer is owed, and while a half-built court still has a seat the organiser
#: can fill. Released otherwise — the two endings release because there is
#: nothing left, and ``ON`` releases because the arranging is **finished** and a
#: game exists. Those are different reasons reaching the same answer, which is
#: exactly why one set cannot serve both readers.
#:
#: Before this set existed the rule read ``not in ENDED``, so ``ON`` held its
#: pair with no expiry: two people who completed a line-up could never challenge
#: each other again in **any** sport and were gone from each other's deck
#: permanently, while ``games_match_history.py`` stated the opposite as settled
#: fact.
ARRANGING = frozenset({Standing.AWAITING_ANSWERS, Standing.LINE_UP_INCOMPLETE})


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
