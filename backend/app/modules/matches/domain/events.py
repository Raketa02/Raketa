"""What happened to a match, said specifically — one name per change.

ADR-0034 takes the ordinary transactional-outbox pattern (ADR-0003) and adds one
obligation that is not ordinary, and that has to be honoured from the first
commit:

> **Every change a support agent would one day need to explain to a player is
> announced as its own named event — never as a generic "match updated".**

That is the whole reason this file is long. The match keeps no history
(ADR-0034), so the announcements *are* the trail: the planned
**playerEventsTracker** is to be built from them and never written alongside
them, and an event published too coarsely is a question a support agent cannot
answer later with a player on the phone. Nothing mechanical catches a coarse
event, which is why ``tests/unit/test_match_events.py`` walks the aggregate and
fails when a mutating method announces nothing, and why no name here is a verb
like *updated* or *changed*.

**Events carry primitives**, as the rating context's do: a sport as its ``str``
value, an instant as a ``datetime``, money as an ``int`` of grosze. They are a
published contract independent of how these Python types are later refactored —
*"not sourcing state from them does not make them private"*.

**Every event names its match**, and nothing carries the whole record. A
consumer that wants the match reads it; an event that carried a snapshot would
be a second copy of the row, ageing from the moment it was written.

A score therefore rides as ``list[list[int]]`` rather than as tuples: JSON has
no tuple, so an event declared with them decodes into something that does not
equal what was published — a durable contract that is only durable in one
direction. The pairs are the wire format `Raketa02/Raketa#74` fixes, and this is
that format, stored and announced identically.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

# ---------------------------------------------------------------------------
# Constitutive — chosen at creation, never recomputed
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MatchPosted:
    """A match exists: this sport, this club, this hour, at this price a seat.

    The only event that carries the constitutive facts, because they are the
    only ones that never change. ``policy_window`` and ``policy_join_cut`` ride
    with it for the reason ADR-0077 gives — the cancellation window in force
    when the match was posted is honoured as booked, so the announcement has to
    say which one that was.
    """

    match_id: UUID
    club_id: UUID
    category_id: UUID
    sport: str
    kind: str
    pay_model: str
    start: datetime
    duration_minutes: int
    seats: int
    share_grosze: int
    counted: bool
    policy_window_minutes: int
    policy_join_cut_minutes: int
    occurred_at: datetime


# ---------------------------------------------------------------------------
# The one mutable constitutive-looking fact, and it is deliberately not one
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MatchStartMoved:
    """The match moved, and every deadline moved with it.

    ADR-0032 keeps ``start`` mutable — *"a moved match is the same match"* — so
    this is an ordinary write and not a cancel-and-repost. It carries **both**
    instants because *what time was this before you moved it* is precisely the
    question a player rings up about, and the record no longer knows.
    """

    match_id: UUID
    moved_from: datetime
    moved_to: datetime
    occurred_at: datetime


# ---------------------------------------------------------------------------
# Occupancy — who is on the court, and who owes for it
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SeatTaken:
    """A player took a seat. Held, and not yet paid for.

    ``filled_a_vacancy`` is the difference between a match filling up and a
    match recovering from somebody leaving, which are two different stories
    about the same count going up.
    """

    match_id: UUID
    seat_index: int
    player_id: UUID
    filled_a_vacancy: bool
    occurred_at: datetime


@dataclass(frozen=True)
class SeatClaimOpened:
    """A player took the exclusive right to buy a seat, for five minutes.

    **Not a seat event**, and it is here beside them because it is what a
    support agent will reach for when somebody asks *why could I not take that
    seat at 18:03* (ADR-0081). The seat itself is untouched — still empty, still
    absent from the fill count — so nothing about occupancy is announced.

    ``expires_at`` rides on it because the deadline is the fact, not the
    duration: a change to the five minutes must not retroactively move a
    deadline already announced.
    """

    match_id: UUID
    claim_id: UUID
    seat_index: int
    player_id: UUID
    expires_at: datetime
    occurred_at: datetime


@dataclass(frozen=True)
class SeatClaimLapsed:
    """A claim ended without the seat being bought, and the seat is on offer again.

    One name for two arrivals, and deliberately: the five minutes running out
    and the match dying underneath the claim are *"one rule ends a claim,
    whatever ended it"* (ADR-0081), and downstream they are one thing — a
    payment that lands afterwards is refunded with cause ``claimLapsed`` either
    way. Which of the two happened is answered by what else is on the outbox at
    the same instant: a cancellation announces itself.

    ``ended_at`` is when the claim stopped being live, which for an expiry is
    the moment its five minutes ran out and **not** the moment a wake noticed —
    a downed worker must not extend anybody's thirty-second cooldown.
    """

    match_id: UUID
    claim_id: UUID
    seat_index: int
    player_id: UUID
    ended_at: datetime
    occurred_at: datetime


@dataclass(frozen=True)
class SeatClaimRedeemed:
    """The claim was spent: the seat is bought, taken and paid in one move.

    Its own name rather than being read off the ``SeatTaken`` beside it,
    because *she bought the seat she was holding* and *somebody was invited onto
    a seat* are two different stories that leave the same occupancy behind.
    """

    match_id: UUID
    claim_id: UUID
    seat_index: int
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SeatPaid:
    """The money for a seat landed.

    Its own announcement rather than a field on ``SeatTaken``: *held* and
    *paid* are two states the card says two different things about, and the gap
    between them is the whole of ``formingHeld``.
    """

    match_id: UUID
    seat_index: int
    player_id: UUID
    share_grosze: int
    occurred_at: datetime


@dataclass(frozen=True)
class SeatVacated:
    """A player gave up a seat, leaving a hole.

    The *hole* is this context's fact. What the leaver recovered is her
    departure's, settled on an axis of its own (ADR-0033), and it is not here —
    which is why this event carries no amount and no outcome.
    """

    match_id: UUID
    seat_index: int
    player_id: UUID
    was_paid: bool
    occurred_at: datetime


@dataclass(frozen=True)
class PlayerDeparted:
    """A player left, and this is what it was worth to her.

    **Beside ``SeatVacated`` and not folded into it**, because they are two
    facts (ADR-0033): that one is the *hole* the match now carries, this one is
    the *money*, and a filler closes the oldest hole while settling the oldest
    unsettled departure — not always the same one. Announcing them together
    would be the single scalar the ADR replaced, wearing an event's clothes.

    ``amount_grosze`` is **absent** rather than zero when nothing was taken:
    ADR-0030 fixes that a pre-commitment leave clears the seat *and* the
    payment, *"so the card can name no amount at all"*, and a zero would invite
    a reader to interpret a blank.

    ``quoted`` is the label she was shown and acted on, and it rides because
    *what was she promised* is the first question a support agent asks and the
    record stops being able to answer it the moment the match moves.
    """

    match_id: UUID
    departure_id: UUID
    seat_index: int
    player_id: UUID
    quoted: str
    amount_grosze: int | None
    occurred_at: datetime


@dataclass(frozen=True)
class DepartureSettled:
    """Her money is decided: no further seat event can change this outcome.

    A departure that took nothing is **born settled**, so this is announced in
    the same breath as ``PlayerDeparted`` for a reversal, and much later — when
    a filler pays, or when the match ends around her — for anybody who paid.
    """

    match_id: UUID
    departure_id: UUID
    player_id: UUID
    outcome: str
    occurred_at: datetime


@dataclass(frozen=True)
class DepartureOutcomeImproved:
    """A settled outcome got better, which is the only way it may move.

    ADR-0030: *"a club-side failure that refunds everybody may improve a settled
    50 % to a full refund; nothing may reduce a settled outcome."* Its own name
    rather than a second ``DepartureSettled``, because *you were refunded half
    and now you are refunded in full* is a different sentence from *you were
    refunded half*, and the ledger cause for it — ``settlementReopened`` — exists
    for exactly this and reaches no card.
    """

    match_id: UUID
    departure_id: UUID
    player_id: UUID
    improved_from: str
    improved_to: str
    occurred_at: datetime


@dataclass(frozen=True)
class SeatsOpened:
    """A private court put seats on the marketplace.

    Unanimous among everybody already paid (ADR-0030), which is why the count
    is announced rather than inferred: *who agreed to sell a seat in my court*
    has no other record.
    """

    match_id: UUID
    open_seats: int
    occurred_at: datetime


@dataclass(frozen=True)
class SeatTransferStarted:
    """A leaver named somebody to take her seat and the handover is running."""

    match_id: UUID
    seat_index: int
    occurred_at: datetime


@dataclass(frozen=True)
class SeatTransferEnded:
    """The handover finished or fell through; the seat is an ordinary seat again."""

    match_id: UUID
    seat_index: int
    occurred_at: datetime


# ---------------------------------------------------------------------------
# Allocation — a claim on contended inventory, and its failure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CourtHeld:
    """A court is being kept aside for this match.

    Announced by the match rather than by the reservation because *why is a
    court being held* is a question about the match. **Which** court is Courts'
    answer, and this deliberately does not repeat it — see ``match.py``.
    """

    match_id: UUID
    held_since: datetime
    occurred_at: datetime


@dataclass(frozen=True)
class CourtReleased:
    """The court went back on sale, and there is still a group to tell."""

    match_id: UUID
    released_at: datetime
    occurred_at: datetime


@dataclass(frozen=True)
class CourtLocked:
    """The club committed a court by hand, outside the ladder.

    A Declaration in ADR-0034's table and an Allocation in effect, and it is
    filed here because that is what it does: no reader can derive that a
    manager decided something, and until playerEventsTracker exists this
    announcement is the only record that they did.
    """

    match_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class HoldExtended:
    """The club published an extension of a hold the ladder had lapsed."""

    match_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class InventoryLost:
    """The last court of the category was sold to somebody else.

    Terminal, and the one ending that is nobody's decision — which is why it
    sits above the cancellations in the ladder and why it is one story and never
    *we raced somebody and lost* (ADR-0035).
    """

    match_id: UUID
    occurred_at: datetime


# ---------------------------------------------------------------------------
# Crossing — a threshold irreversibly passed
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MatchCommitted:
    """Everybody is bound to this match now.

    ``on_fill`` distinguishes *the deadline arrived and the match was full* from
    *the match filled after its deadline had already passed*, which are the two
    sentences the card has to choose between — and the difference is not
    derivable an hour later.
    """

    match_id: UUID
    committed_at: datetime
    on_fill: bool
    occurred_at: datetime


# ---------------------------------------------------------------------------
# Declaration — an outside actor's decision
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MatchCancelledByClub:
    """A manager cancelled it. **No reader can derive this** — ADR-0034 says so
    in terms, and it is why this is not filed with the two receipts below."""

    match_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class MatchCancelledForWeather:
    """The weather cancelled it. The club's decision, told as its own story."""

    match_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class MatchCancelledIncomplete:
    """It never filled, and the refund, the court release and the notice are done.

    A **receipt** on a conclusion the clock already reached: the situation
    derives without it, and the flag records only that the money moved. That is
    ADR-0034's fix for a downed timekeeper stated as a rule — *the money is
    delayed and the truth never is*.
    """

    match_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class MatchCancelledAtCheckpoint:
    """It was still short at the checkpoint, and the same receipt applies."""

    match_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class NoShowRecorded:
    """Somebody who paid did not turn up."""

    match_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class ScoreProposed:
    """A score went on the table, and who put it there.

    ``proposals`` is the count ADR-0034 keeps instead of a list: *"a count, not
    a sequence"*. The conversation belongs to the tracker these announcements
    feed, which is exactly the shape a support agent reads it in.
    """

    match_id: UUID
    proposed_by: UUID
    sets: list[list[int]]
    proposals: int
    occurred_at: datetime


@dataclass(frozen=True)
class ResultAgreed:
    """The score settled — by agreement, or by the silence that confirms it.

    ``by_silence`` is not derivable from the record afterwards, and it is the
    difference between *we agreed* and *nobody answered*, which ADR-0048 makes
    the same outcome and a support agent does not.
    """

    match_id: UUID
    sets: list[list[int]]
    by_silence: bool
    occurred_at: datetime
