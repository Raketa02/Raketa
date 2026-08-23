"""One ladder resolves a situation, and one wake function reads the same boundaries.

``situation(record, viewer, now)`` is the single resolver over a single closed
enumeration of **thirty-six** members, and **the order of the ladder is the
specification** — tested top to bottom, first match wins, reordering changes
behaviour. Called with a viewer it may yield ``WAITLISTED``, ``SEAT_OFFERED`` or
``SEAT_OPENED``; called without, it cannot. The absolute form is *the same
function with the parameter absent*, never a second derivation, so there is
nothing for a consistency suite to catch
(``docs/adr/0040-one-ladder-resolves-a-situation.md``).

**A situation is a sentence.** Where one name would make a client choose between
two sentences from a fact on the wire, it is two names instead
(``docs/adr/0072-two-sentences-are-two-situations-and-a-leaver-is-a-third-audience.md``)
— because a boolean whose only job is to pick which sentence the phone writes
*is* a rule on the phone wearing a different hat, and it degrades in the wrong
direction: an unknown name loses a sentence, a misread boolean prints a
confident wrong fact.

**Every other state vocabulary is a total projection off this one**, owned by
the consumer that needs it and asserted exhaustive at module load — never a
second ladder over the same record. ``MatchPhase`` in
``app/engines/matchmaking.py`` is the first of them.

**Four defects of the ladder as published are closed here rather than recorded.**
``protectedCourt`` and ``protectedLate`` are gone: reaching them needs a
committed match that is neither full nor short a seat somebody vacated, and no
writer produces one — so the fact combination is refused rather than named.
``formingLate`` no longer answers *is there a court* two ways under one name.
The recovery rung terminates, because a vacancy is a hole while it is a hole and
a filler closes it. And the twenty-four hours after an uncommitted departure are
mechanical rather than documented.

**Everything that varies by audience and is not one of the three viewer rungs is
rendering, downstream.** The leaver's card is the match's card rendered for
somebody who used to hold a seat; the result affordance is suppressed for a
leaver and for a standby player without moving either off ``NEEDS_RESULT``; the
non-member money line is a rewrite over a situation that has already resolved.
"""

from __future__ import annotations

from enum import Enum
from typing import Never

from app.kernel.holds import (
    Hold,
    HoldKind,
    HoldReason,
    court_hold,
    hold_boundaries,
    is_held,
)
from app.kernel.invariants import InvariantViolated, invariant
from app.kernel.matches import (
    Boundary,
    MatchKind,
    MatchRecord,
    OfferKind,
    PayModel,
    Viewer,
    WakeReason,
    born_late,
    claim_boundaries,
    committed_on_fill,
    deadlines,
    door_code_at,
    filled,
    is_full,
    is_terminal,
    match_end,
    result_window,
    seat_count,
    vacancy_expires_at,
)
from app.kernel.time import Instant


class Situation(str, Enum):
    """What a match is doing, in thirty-six sentences and no more.

    Written in ladder order, so that reading the enumeration is reading the
    specification. The values cross the wire as a generated union
    (``docs/adr/0006-backend-owns-api-contract.md``), which is what makes a
    client missing a row a compile error in that client's own build rather than
    something a cross-application suite has to go looking for.
    """

    # 1-4 · cancelled. Inventory loss is tested first because it *also* sets the
    # club cancellation, and without the earlier test every lost court would
    # read as weather — the one risk the player was carrying, never named.
    INVENTORY_LOST = "inventoryLost"
    CANCELLED_CLUB = "cancelledClub"
    CANCELLED_INCOMPLETE = "cancelledIncomplete"
    CANCELLED_CHECKPOINT = "cancelledCheckpoint"

    # 5 · played. Cancellation beats play: a club cancelling at 19:00 for an
    # 18:30 match must read cancelled, because nobody played.
    PLAYED_NO_SHOW = "playedNoShow"
    PLAYED_SHORT = "playedShort"
    COMPLETED = "completed"
    PLAYED_NO_SCORE = "playedNoScore"
    CONFIRM_RESULT = "confirmResult"
    NEEDS_RESULT = "needsResult"

    # 6 · a seat is on the table for this viewer.
    SEAT_OFFERED = "seatOffered"
    SEAT_OPENED = "seatOpened"

    # 7 · queueing for a seat rather than holding one.
    WAITLISTED = "waitlisted"

    # 8 · somebody's own court.
    PRIVATE_OPEN = "privateOpen"
    PRIVATE_FULL = "privateFull"
    PRIVATE_PARTIAL = "privatePartial"
    PRIVATE_RESERVED = "privateReserved"

    # 9 · a committed match lost somebody, and the money is still moving.
    REPLACEMENT_TRANSFER = "replacementTransfer"
    RESCUE_LATE = "rescueLate"
    RESCUE = "rescue"
    REPLACEMENT = "replacement"

    # 10 · somebody left before commitment, recently.
    PROTECTED_BACK = "protectedBack"
    FORMING_BACK = "formingBack"

    # 11 · complete. Full beats protected: reporting the court state to a
    # complete group is the less useful of the two facts.
    READY = "ready"
    CONFIRMED_ON_FILL = "confirmedOnFill"
    CONFIRMED = "confirmed"
    FULL = "full"

    # 12 · posted after its own commitment deadline, which is not the same
    # sentence as a deadline that has since passed.
    FORMING_LATE_HELD = "formingLateHeld"

    # 13 · a court is being kept aside.
    CLUB_HELD = "clubHeld"
    HELD_SOFT = "heldSoft"

    # 14-17 · forming.
    HELD_RELEASED = "heldReleased"
    FORMING_HELD = "formingHeld"
    FORMING_LATE = "formingLate"
    FORMING = "forming"

    # W1-W2 · the club's two amendments, applied after the ladder so that a
    # cancelled or played match is never relabelled as a court state.
    HELD_STALE = "heldStale"
    HELD_EXTENDED = "heldExtended"


#: The whole enumeration is thirty-six, and the count is pinned rather than
#: counted, so that a member arriving or leaving is a decision somebody made in a
#: diff. Thirty-three after two structurally impossible names were deleted, plus
#: the two offer sentences and the second half of `formingLate` (ADR-0072).
SITUATION_COUNT = 36

invariant(
    len(Situation) == SITUATION_COUNT,
    f"the ladder resolves {len(Situation)} names, not {SITUATION_COUNT}",
)

#: The keys a club's cap may rewrite: a hold it has taken back leaves a match
#: describing a released court rather than a forming one. Both halves of the
#: split `formingLate` are here, because splitting a name must not quietly
#: narrow what a wrapper covers.
_STALE_REWRITES = frozenset(
    {
        Situation.HELD_RELEASED,
        Situation.FORMING,
        Situation.FORMING_LATE,
        Situation.FORMING_LATE_HELD,
    }
)

#: The keys a club's published extension may rewrite. `HELD_SOFT` is here and
#: not in the stale set because an extension turns a lapsed hold back into a
#: held court, and the card should say on whose authority.
_EXTENDED_REWRITES = _STALE_REWRITES | {Situation.HELD_SOFT}


def situation(
    record: MatchRecord,
    viewer: Viewer | None,
    now: Instant,
) -> Situation:
    """What this match is doing, for this viewer, at this instant.

    Pure: a function of the record and the clock, with no I/O, no repository and
    no ambient time. Two calls with the same three arguments are the same
    answer, which is what makes a scrubbed clock reproducible and a wake a look
    rather than an instruction.
    """

    hold = court_hold(record, now)
    return _amended(_ladder(record, viewer, now, hold), hold)


def next_wake(record: MatchRecord, now: Instant) -> Boundary | None:
    """The next boundary this match could resolve differently at, or `None`.

    Beside the ladder deliberately, and this is the whole of the argument: **a
    threshold cannot exist in the ladder and be missing from the schedule** if
    both read one list. The timekeeper stores the answer as a column and
    recomputes it on every write (``Raketa02/Raketa#72``), so no boundary is
    hand-maintained anywhere downstream.

    Strictly later than `now`: a candidate exactly at `now` is not a future
    wake, which is what makes the wake chain terminate rather than re-arm itself
    at the same instant for ever.

    **A wake is a look, not an instruction.** The handler re-derives from the
    record, so a late wake changes *when* we look and never *what we find*. The
    name this returns beside the moment is a **label** — half of
    ``{matchId}:{threshold}:{scheduledFor}`` — and nothing branches on it: it was
    computed at a past write, and the match may have moved since. Neither field
    is ever serialised onto a card.

    The candidate set depends on the seat count, so it must be recomputed on
    every write: a match on two paid seats wakes at T-12h, and the same match
    after a third payment wakes at T-4h instead.

    Viewer-relative rungs contribute nothing, because they read no clock. An
    offer's own expiry belongs to the cascade that made it, not to the match.
    """

    if is_terminal(record):
        return None
    ahead = [moment for moment in _boundaries(record) if moment.at > now]
    return min(ahead, key=lambda moment: moment.order) if ahead else None


def next_wake_at(record: MatchRecord, now: Instant) -> Instant | None:
    """The same answer with its name dropped, for a caller that wants a moment.

    Kept because the wake property suite reads it and because most callers do
    not care which threshold it is. The timekeeper does: ``wake_reason`` is half
    of ``{matchId}:{threshold}:{scheduledFor}``.
    """

    wake = next_wake(record, now)
    return None if wake is None else wake.at


def _ladder(
    record: MatchRecord,
    viewer: Viewer | None,
    now: Instant,
    hold: Hold,
) -> Situation:
    """The seventeen rungs, in the order that is the specification."""

    when = deadlines(record)
    seats = seat_count(record)
    paid = filled(record)

    # 1-4 · cancelled, and the order inside the group is load-bearing.
    if record.inventory_lost:
        return Situation.INVENTORY_LOST
    if record.club_cancelled or record.weather:
        return Situation.CANCELLED_CLUB
    if record.form_cancelled:
        return Situation.CANCELLED_INCOMPLETE
    if record.checkpoint_cancelled:
        return Situation.CANCELLED_CHECKPOINT

    # 5 · played. This rung deliberately has no membership test: a standby
    # player and a leaver both resolve to the post-play situation, and the
    # affordance to enter a score is what is withheld from them, downstream.
    # Moving the membership question above the cancellations would answer *am I
    # in this at all* before *what happened to it*, and ADR-0030 settled that
    # the suppression is the fix rather than the rung order.
    if now >= match_end(record):
        if record.no_show:
            return Situation.PLAYED_NO_SHOW
        if paid < seats:
            return Situation.PLAYED_SHORT
        if record.result_agreed:
            return Situation.COMPLETED
        if now >= result_window(record):
            return Situation.PLAYED_NO_SCORE
        if record.score_proposed:
            return Situation.CONFIRM_RESULT
        return Situation.NEEDS_RESULT

    # 6 · a seat on the table, above the queue that produced it: somebody who
    # asked about this match is first in the invitation ladder, and telling her
    # she is still queueing while the seat is hers to take would be the one
    # sentence that makes standby worthless.
    if viewer is not None and not viewer.holds_seat and viewer.offer is not None:
        if viewer.offer is OfferKind.EXCLUSIVE:
            return Situation.SEAT_OFFERED
        return Situation.SEAT_OPENED

    # 7 · the one rung ADR-0040 named, and the reason the resolver takes a
    # viewer at all.
    if viewer is not None and not viewer.holds_seat and viewer.on_standby:
        return Situation.WAITLISTED

    # 8 · a private court, which is a different money model and not a variation
    # on this one.
    if record.kind is MatchKind.PRIVATE:
        if record.open_seats > 0:
            return Situation.PRIVATE_OPEN
        if record.pay_model is PayModel.SPLIT:
            # The moment the last share is paid the owner stops carrying the
            # court, and the guarantee she was told about is discharged. Under
            # the published ladder this resolved to `privatePartial`, whose card
            # goes on naming a liability against a court that has just filled.
            if is_full(record):
                return Situation.PRIVATE_FULL
            return Situation.PRIVATE_PARTIAL
        return Situation.PRIVATE_RESERVED

    # 9 · recovery, above full and above the court group. A committed match that
    # lost a player is one seat short, and describing that as an ordinary
    # forming match is a catastrophic thing to tell somebody whose money is at
    # stake. It terminates because the vacancy does: a filler closes the hole,
    # and the rung stops firing on the same read.
    if record.open_vacancies and record.committed_at is not None:
        if record.transferring:
            return Situation.REPLACEMENT_TRANSFER
        if now >= when.check:
            return Situation.RESCUE_LATE
        if now >= when.rescue:
            return Situation.RESCUE
        return Situation.REPLACEMENT

    # 10 · somebody left before commitment. The twenty-four hours are the
    # mechanism the documents promised and never had: past them the match is an
    # ordinary forming match again, rather than pinned in a recovery state
    # because a flag was never cleared.
    expires_at = vacancy_expires_at(record)
    if expires_at is not None and now < expires_at:
        return Situation.PROTECTED_BACK if is_held(hold) else Situation.FORMING_BACK

    # 11 · complete.
    if is_full(record):
        if now >= door_code_at(record):
            return Situation.READY
        if record.committed_at is not None:
            if committed_on_fill(record):
                return Situation.CONFIRMED_ON_FILL
            return Situation.CONFIRMED
        return Situation.FULL

    # 12 · born past its own commitment deadline. Above the court group because
    # for such a match *the deadline has passed* is the wrong sentence and *a
    # court is held* is the right one — and below the full group because a
    # complete match has a better thing to say than either.
    if now >= when.commit and born_late(record):
        return Situation.FORMING_LATE_HELD if is_held(hold) else Situation.FORMING_LATE

    # 13 · a court is being kept aside, and the card says on what terms.
    if is_held(hold):
        if hold.why is HoldReason.CLUB:
            return Situation.CLUB_HELD
        if hold.kind is HoldKind.SOFT:
            return Situation.HELD_SOFT
        return _impossible(
            "a hard court hold that is neither the club's nor a full or private "
            f"match's: {hold.why.value}. A committed match is either complete or "
            "short a seat somebody vacated, and both are resolved above this "
            "rung — which is why `protectedCourt` and `protectedLate` are not "
            "names in the enumeration"
        )

    # 14 · the court went back on sale, and there is still a group to tell.
    if record.released_at is not None and paid >= 2 and now < when.check:
        return Situation.HELD_RELEASED

    # 15 · somebody holds a seat nobody has paid for.
    if any(seat.taken and not seat.paid for seat in record.seats):
        return Situation.FORMING_HELD

    # 16-17 · forming, late or otherwise.
    if now >= when.commit:
        return Situation.FORMING_LATE
    return Situation.FORMING


def _amended(base: Situation, hold: Hold) -> Situation:
    """The club's two amendments, applied after the ladder and never inside it.

    Last, so that a stale hold on a cancelled match still reads as a
    cancellation. A court state must never relabel a match that is over.
    """

    if hold.why is HoldReason.STALE and base in _STALE_REWRITES:
        return Situation.HELD_STALE
    if hold.why is HoldReason.EXTENDED and base in _EXTENDED_REWRITES:
        return Situation.HELD_EXTENDED
    return base


def card_clock(
    record: MatchRecord,
    now: Instant,
    *,
    claim_expires_at: Instant | None = None,
) -> Instant | None:
    """The one moment a card counts down to, or nothing.

    ADR-0073 gives a card **exactly one clock slot** and fixes which moment
    fills it with a rule rather than with thirty-six judgements:

        *The clock is the next moment at which something happens to the viewer
        whether they act or not.*

    That is the soonest boundary **the ladder itself reads**, ahead of now — a
    boundary is by definition an instant at which this match resolves to a
    different sentence, and a sentence changing under the player is exactly
    something happening to her. So the rule is one line over the list
    ``next_wake`` already reads, and a threshold cannot be in the ladder and
    missing from the countdown for the same reason it cannot be missing from
    the schedule.

    **It is not ``next_wake``, and the one difference is the whole difference.**
    A seat claim's five minutes are in the schedule and are *not* a boundary any
    rung reads (ADR-0081 refuses a thirty-seventh situation for it), so a
    stranger's claim lapsing would otherwise point this viewer's countdown at
    five minutes that are about somebody else. What replaces it is
    ``claim_expires_at`` — **the viewer's own** claim, which is about her and
    not about the match, and which wins outright when she holds one because a
    claim lapsing in five minutes is the next thing that happens to her whether
    she acts or not.

    **A card that is over or cancelled counts to nothing.** A terminal match has
    no boundaries at all, and a played one runs out of them at its result
    window, so the empty slot falls out of the same rule rather than being a
    case beside it.

    Always-the-start-time was refused because it ticks five hundred hours down
    to a game nobody is worried about while the hold expires in silence; the
    next-moment-you-can-still-act was refused for the opposite reason — a seat
    being rescued is precisely when a player can do nothing and precisely when
    she most needs to see the deadline. **The clock is the app's warning, not
    its to-do list.**
    """

    if claim_expires_at is not None and now < claim_expires_at:
        return claim_expires_at
    ahead = [moment for moment in _ladder_boundaries(record) if moment.at > now]
    return min(ahead, key=lambda moment: moment.order).at if ahead else None


def _boundaries(record: MatchRecord) -> tuple[Boundary, ...]:
    """Every instant the ladder compares the clock against, plus the hold's own.

    Conditioned exactly as the rungs that read them are, so an ordinary match is
    not woken for a threshold no rung will look at — and the hold ladder is
    *asked* for its thresholds rather than having them restated here, which is
    the half that would otherwise drift.

    **A claim's expiry is here and not in ``_ladder_boundaries``**, and that
    split is the one thing separating the schedule from the countdown: the
    reaper has to be woken for a claim nobody's card mentions, and no card may
    count down to a claim that is not the viewer's.
    """

    return (*_ladder_boundaries(record), *claim_boundaries(record))


def _ladder_boundaries(record: MatchRecord) -> tuple[Boundary, ...]:
    """Every instant a **rung** compares the clock against, plus the hold's own.

    Conditioned exactly as the rungs that read them are, so an ordinary match is
    not woken for a threshold no rung will look at — and the hold ladder is
    *asked* for its thresholds rather than having them restated here, which is
    the half that would otherwise drift.

    **A terminal match has none**, which is a fact about the ladder rather than
    a short cut: rungs 1-4 answer before any rung reads a clock, so no later
    threshold can change what a cancelled match says. ``next_wake`` states the
    same thing for itself, and ``card_clock`` gets *"a card that is over or
    cancelled counts to nothing"* from here instead of from a case of its own.
    """

    if is_terminal(record):
        return ()

    when = deadlines(record)

    candidates = [
        Boundary(WakeReason.CHECKPOINT, when.check),
        Boundary(WakeReason.JOIN_CUT, when.join_cut),
        Boundary(WakeReason.PLAY, when.play),
        Boundary(WakeReason.DOOR_CODE, door_code_at(record)),
        Boundary(WakeReason.MATCH_END, match_end(record)),
        Boundary(WakeReason.RESULT_WINDOW, result_window(record)),
        # Asked for rather than restated, exactly like the ladder's own tiers,
        # so a tier cannot exist in one and be missing from the other.
        *hold_boundaries(record),
    ]

    # A committed match never compares the clock against its own commitment
    # deadline: it is either complete or short a seat somebody vacated, and both
    # resolve above every rung that reads `commit`.
    if record.committed_at is None:
        candidates.append(Boundary(WakeReason.COMMITMENT, when.commit))

    if record.open_vacancies:
        if record.committed_at is not None:
            candidates.append(Boundary(WakeReason.RESCUE, when.rescue))
        else:
            expires_at = vacancy_expires_at(record)
            if expires_at is not None:
                candidates.append(
                    Boundary(WakeReason.VACANCY_DECAY, expires_at)
                )

    return tuple(candidates)


def _impossible(message: str) -> Never:
    """Refuse a record no writer can produce.

    Raised rather than returned: this is not a legitimate domain state with no
    answer, it is a fact combination that means something upstream has lost
    track of a seat, and no caller can do anything sensible with it.
    """

    raise InvariantViolated(message)
