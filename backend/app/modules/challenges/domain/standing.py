"""What a challenge **is** right now, read off the seats and the clock.

**Derived, never stored** (#221). A status column would be wrong for the whole
gap between a deadline passing and a sweep noticing, and it would be the copy
that gets believed. So there is no status field on the aggregate, no status
column in the store, and this function is the only place a standing exists.

Six values, and five of them are what the seats and the clock can answer for.
The twenty card states the prototype draws are a *presentation* vocabulary
spanning money, booking and results that nothing here owns.

**The sixth is the one exemption this module holds, and it is written down so it
stays one.** A withdrawal is a decision a person took, and there is nothing in
the seats to fold it out of — so it is the one standing an event announces, and
the rule that lets it is *an event may announce a conclusion only when no
arrangement of the seats could reach it* (``docs/adr/0142`` §3). The event is not
a second place for the fact to be true; it is the only place.

*Challenge sent* and *Challenge for you* are **not** two standings. They are one
standing read from two sides, which is why nothing here takes a reader.

**And when it became that**, for the three that are endings
([#388](https://github.com/Raketa02/Raketa/issues/388)). :func:`ended_at_of` is
the same fold's second half and lives beside it rather than in a module of its
own, because *which ending was this* and *when did it happen* are one question
asked twice — the first is :func:`_how_it_ended` and the second reads the same
seats. Derived, never stored, for the reason above and one more: an ending
instant is the only thing on a challenge a client subtracts from its own clock,
so a stored copy would go stale in the one place staleness is visible.
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable, Mapping, final
from uuid import UUID

from app.kernel import Instant, invariant
from app.modules.challenges.domain.seats import Seat, SeatAnswer


@final
class Standing(str, Enum):
    """The six standings, as codes. A client's words are the client's own."""

    #: Somebody's answer is still owed and still wanted.
    AWAITING_ANSWERS = "AWAITING_ANSWERS"
    #: Every seat is accepted. **No event says this** — it is the fold's answer,
    #: and an event announcing it would be a second place for it to be true.
    ON = "ON"
    #: Nobody is waiting, two or more are in, and a seat is open. The state
    #: the builder is re-entered from — and **not a waiting
    #: room**: the people who are in are in, and a conversation between them has
    #: already started. **Reached after ``ON`` too** (``docs/adr/0162``): a
    #: court whose line-up completed into a game and then lost somebody is half
    #: built again, and it is this standing with no change to the fold that
    #: derives it — the game stands, with that seat open, until the next
    #: completed line-up re-seats it.
    LINE_UP_INCOMPLETE = "LINE_UP_INCOMPLETE"
    #: Over, and somebody said no — or, having said yes, left
    #: (``docs/adr/0165`` §3: a departure is a no).
    DECLINED = "DECLINED"
    #: Over, and nobody said anything.
    LAPSED = "LAPSED"
    #: Over, and the organiser ended it. **The one value here that no
    #: arrangement of the seats reaches**: nobody said no and nobody was silent,
    #: so it can reuse neither ending, and a court that was withdrawn still
    #: holds the acceptance that put it in ``LINE_UP_INCOMPLETE``. It arrives on
    #: the fold from ``ChallengeWithdrawn`` and from nowhere else.
    #:
    #: **Not ``STOOD_DOWN``.** The root ``CONTEXT.md`` owns *stands down*
    #: platform-wide for a term that cannot be evaluated, and one word means one
    #: idea in the file that owns it. *Call off* is what a withdrawal — or the
    #: departure that leaves one player on the court (``docs/adr/0165`` §3) —
    #: does to the **game** a reopened court became (``docs/adr/0163``), and
    #: the game's own standing carries that word.
    WITHDRAWN = "WITHDRAWN"


#: The three standings that mean *this challenge has ended* — there is nothing
#: left to arrange and nothing left to do. Read by ``Challenge.invite``, which
#: refuses to seat anybody into one, and by the standing the client prints.
#:
#: **``WITHDRAWN`` is the third, and it is a third *kind* of ending** rather than
#: a spelling of either of the other two (``docs/adr/0142`` §4). A decline is
#: somebody's judgement and a lapse is somebody's silence; a withdrawal is the
#: organiser ending an arrangement nobody was going to complete. Filing it as
#: either would restate a decision as one of the two facts *answers challenges*
#: exists to keep apart.
#:
#: **The mutual mint used to read it and no longer does** (``docs/adr/0152``).
#: It asked *does a challenge already stand between these two*, which for a
#: mutual-born challenge answers *yes* for the life of the database: every seat
#: is accepted at birth, so it can never lapse, never decline, and 0142 §2
#: denies ``ON`` the withdraw exit. A guard about whether an act was already
#: performed had inherited a *state*'s eternity. What the mint asks now is
#: :data:`ARRANGING` — the same question the send asks — plus one of its own
#: about the game the last mutual minted.
#:
#: **``ON`` is not here, and adding it would be the wrong way to release a pair.**
#: A challenge every seat accepted is not over: it produced a game, which is the
#: opposite of nothing being left. See :data:`ARRANGING`.
ENDED = frozenset({Standing.DECLINED, Standing.LAPSED, Standing.WITHDRAWN})

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
#: **It has a second reader now, and it is the same question** — the card block
#: on the detail read (``docs/adr/0143`` §8). *A card is part of an arrangement
#: being decided, and it stops when the deciding does*, which is this set's own
#: sentence read one surface over: ``DECLINED`` and ``LAPSED`` draw the
#: arrangement and the handle alone because the pair has released, and ``ON``
#: draws neither because the arranging is **finished** and the game's own screen
#: owns it. Stated on the two that draw a card rather than on the ones that do
#: not, so a standing added later is silent by default.
ARRANGING = frozenset({Standing.AWAITING_ANSWERS, Standing.LINE_UP_INCOMPLETE})


def standing_of(
    seats: Iterable[Seat],
    *,
    now: Instant,
    withdrawn: bool,
    game_opened: bool,
) -> Standing:
    """The challenge's standing, from its seats, this instant, and the two things
    about it the seats cannot hold.

    The order of the questions is the design, and each rung is a decision:

    **Was it withdrawn?** The one question here that is not about the seats, and
    it is asked first because every other answer is still *yes*: the acceptance
    that put this court in ``LINE_UP_INCOMPLETE`` is still on it, so a fold that
    read the seats first would answer with the standing the organiser has just
    ended. ``withdrawn`` is **stated by every caller and never defaulted**, so a
    second reader of this function has to say which challenge it is asking about
    rather than inheriting an answer.

    **Is the court deserted?** *At most one player on it, and nobody still
    deciding* (``docs/adr/0165`` §3, :func:`deserted`). A court with two or more
    people on it is a court; a court with one, once nobody is still deciding, is
    not — and **the organiser is a player in that rule**. It used to ask *is
    anybody but the organiser still in it*, which filed the organiser alone as
    over and any other player alone as ``LINE_UP_INCOMPLETE`` for good; the
    organiser could not leave then, and can now. A decline reopens that one seat
    and disturbs nothing else, because the people who already agreed did nothing
    wrong and are already talking to each other; but when the last of them is
    gone there is nobody left to keep faith with, and what stands is one person
    on an empty court. Singles gets the right answer for free.

    **Unless the court has been a game** (``docs/adr/0162`` §2), which is the
    second fact the seats cannot hold and is stated by every caller for the same
    reason. One person alone on a court whose others *left* is not somebody who
    never sent: a game stands, with a plan, a room and a record. So this rung is
    skipped for such a court, and it can reach neither ending by its seats — its
    exits are a re-seat, the act that calls the game off, and the departure that
    deserts it, which asks :func:`deserted` itself and calls the game off one
    layer up. ``game_opened`` is folded off the acceptance that completed the
    line-up rather than read off the seats, because a re-seat gives the
    departed's position to the newcomer, and a court whose newcomer then
    declined would have no seat left that said so.

    **Is an answer still owed?** *Awaiting* outranks *line-up incomplete*
    deliberately. A half-built padel court is not re-entered into the builder
    while somebody is still deciding — *a one-to-one padel challenge is half a
    game*, and it is the **acceptance** that produces `LINE_UP_INCOMPLETE`, not
    the empty seats it was sent with.

    **Is every seat accepted?** Then it is on, with no special case for the
    organiser and none for singles: their seat is accepted from birth, which is
    what makes *every seat accepted* the whole of the completion rule.
    """

    if withdrawn:
        return Standing.WITHDRAWN
    seats = tuple(seats)
    if not game_opened and deserted(seats, now=now):
        return _how_it_ended(seats)
    if any(seat.is_awaiting_at(now) for seat in seats):
        return Standing.AWAITING_ANSWERS
    if all(seat.is_accepted() for seat in seats):
        return Standing.ON
    return Standing.LINE_UP_INCOMPLETE


def deserted(seats: Iterable[Seat], *, now: Instant) -> bool:
    """Whether at most one player is on this court and no seat is awaiting an
    answer — **the ending rule** (``docs/adr/0165`` §3), organiser-blind.

    One function with two readers, and that is the point. Before a game the
    fold reads it and reaches one of the two endings; on a game the fold does
    not end the court (``docs/adr/0162`` §2) and the **departure** reads it
    instead, to call the game off in its own transaction. It is written here
    rather than in the use case because the game's own record cannot answer it:
    a game's line-up cannot tell an open seat from one that is *asked*, so a
    game with one player seated and a fill pending would read as deserted there
    and is not — only the challenge knows the difference, which is
    ``docs/adr/0142`` §3's test passed from the other side.

    *On it* is an accepted seat; *deciding* is a seat awaiting an answer whose
    day has not run out. A seat past its deadline with nothing in it is neither,
    whether or not a sweep has been past.
    """

    seats = tuple(seats)
    on_it = sum(1 for seat in seats if seat.is_accepted())
    return on_it <= 1 and not any(seat.is_awaiting_at(now) for seat in seats)


#: The two answers that are somebody's judgement about this court: a no, and
#: — since ``docs/adr/0165`` §3 — a departure. Somebody who accepted and then
#: left made a decision about these people, and a court they emptied is a
#: refused court, never a lapsed one.
_A_NO = frozenset({SeatAnswer.DECLINED, SeatAnswer.LEFT})


def _how_it_ended(seats: tuple[Seat, ...]) -> Standing:
    """Which of the two endings this was: somebody's no, or everybody's silence.

    **A no outranks silence, whatever order the two arrived in.** Somebody made a
    judgement about this challenge and silence is not one, so a challenge that
    was refused is a refused challenge; which clock happened to run out first is
    an accident of when each seat was invited, and a standing that turned on it
    would change meaning overnight without anybody doing anything. **A departure
    is a no** and not a lapse, for the same reason: it is a judgement.
    """

    if any(seat.answer in _A_NO for seat in seats):
        return Standing.DECLINED
    return Standing.LAPSED


def ended_at_of(
    seats: Iterable[Seat],
    *,
    now: Instant,
    updated_at: Instant,
    withdrawn_at: Instant | None,
    game_opened: bool,
    departed_at: Mapping[UUID, Instant],
) -> Instant | None:
    """**When** this challenge ended, or ``None`` because it has not.

    It takes ``now`` and folds the standing itself rather than being handed one,
    so the two halves of the answer cannot be read against two instants: a
    caller holding one reading of the clock gets both from it, and there is no
    parameter through which a standing folded a second earlier could arrive.

    **The ending is the last departure, and not the ending's own name.** A no
    outranks silence whatever order the two arrived in (:func:`_how_it_ended`),
    so a ``DECLINED`` court may have gone on standing for two days *after* the
    no — until the last seat still deciding ran out. What ended it is the latest
    instant at which one of the people asked left, whichever kind of leaving
    each of theirs was; dating the challenge from the decline alone would retire
    the row while the court was still live. **The organiser's own seat counts**
    now that they can leave it (``docs/adr/0165`` §1): a court B is alone on
    ended when the organiser walked out, and that is a seat like any other here.

    **Three of the four are exact and the decline is an upper bound.** A lapse
    *is* a deadline passing, so the instant is on the seat already, recorded or
    not; a withdrawal is a decision somebody took and the decision carries its
    own moment; and so does a departure, which is why the aggregate folds
    ``departed_at`` off ``SeatLeft`` and hands it in — bounding one by the stream's
    last event would let a sweep appending a lapse weeks later move the ending,
    the thing #388 stopped the withdrawal doing. Nothing anywhere holds **when
    somebody declined** — dating an answer is the history walk's job and
    deliberately not the fold's, because an answer happened to the court *as it
    stood then* (``event_sourced_challenge_history.py``) — so a decline is
    bounded by the two facts this fold does hold, and the bound is late rather
    than early. That is the safe direction for the reader it has: a row that
    outstays its shelf life is news gone stale, and one retired early is a
    player never learning a seat reopened.
    """

    seats = tuple(seats)
    standing = standing_of(
        seats,
        now=now,
        withdrawn=withdrawn_at is not None,
        game_opened=game_opened,
    )
    if standing not in ENDED:
        return None
    if standing is Standing.WITHDRAWN:
        return withdrawn_at
    return max(
        (
            _left_at(seat, updated_at=updated_at, departed_at=departed_at)
            for seat in seats
            if seat.player_id is not None and seat.is_open_at(now)
        ),
        # **A court with nobody to have departed.** One person alone among
        # empty seats folds to ``LAPSED``, and the aggregate cannot reach it — a
        # send needs an invitee and a fill needs somebody new — but hand-built
        # seats can, and a read is the wrong place to raise from. The last thing
        # that happened to the stream is the honest upper bound.
        default=updated_at,
    )


def _left_at(
    seat: Seat, *, updated_at: Instant, departed_at: Mapping[UUID, Instant]
) -> Instant:
    """When the person in this open seat left it.

    **Every way an occupied seat opens carries its instant, or a bound on it.**
    A decline and a lapse are both answers to something somebody was asked, and
    ``Seat`` refuses a seated player holding neither an acceptance nor a day.
    For a lapse the deadline *is* the answer — the window closing is the
    leaving, which is why no sweep needs to have run. A departure is a decision
    somebody took and the aggregate folds its instant off the event
    (``docs/adr/0165`` §3): a ``LEFT`` seat may carry no deadline at all — the
    organiser's, a mutual-born pair's — and one that does was met, not missed,
    so the deadline bounds nothing about when they left. A ``LEFT`` seat with no
    departure behind it is a broken fold rather than a state, and it raises.

    **A decline takes the smaller of the deadline and the stream's own instant.**
    Either alone is an upper bound and neither dominates: a court answered and
    then left alone is dated by the stream, and one a sweep appended a lapse to
    weeks later is dated by the deadline — which is what stops this reading
    moving when a loop runs.

    **Not a method on ``Seat``**, though it reads mostly a seat's fields. Which
    two facts bound a decline is the *fold's* policy and one of them is the
    challenge's — a seat that took ``updated_at`` would be a value object
    reading its container, and the next reader would take it for a fact the seat
    holds.
    """

    if seat.answer is SeatAnswer.LEFT:
        player_id = invariant(
            seat.player_id, f"a left seat with nobody in it: {seat!r}"
        )
        return invariant(
            departed_at.get(player_id),
            f"a departure with no instant behind it: {seat!r}",
        )
    deadline = invariant(seat.answer_by, f"an open seat with no deadline: {seat!r}")
    if seat.answer is SeatAnswer.DECLINED:
        return min(deadline, updated_at)
    return deadline
