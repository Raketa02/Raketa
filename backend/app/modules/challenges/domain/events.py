"""The Challenges context's domain events — **eight, and one of them a conclusion**.

Events carry **primitive** fields, so their wire format survives any later
refactor of the Python types: a sport, a mode and a window as their codes, a
player as a ``str`` uuid, and a whole seat as one string (``seats.py``).

**Two openings.** ``ChallengeSent`` is the ordinary one: an organiser with an
arrangement, asking everybody on a built court at once. ``ChallengeOpened
FromMutualInterest`` is the deck's: two people who each said *Let's play* to the
other, so both seats are accepted from birth, there is no deadline anywhere on
it and there is no arrangement to propose. It is a **distinct event rather than a
flag**, because a nullable ``answer_by`` is how a later reader invents a deadline
that never existed.

**Three answers, one per seat, one player each.** ``SeatAccepted`` is published
per acceptance and never once at the end: each accept is consequential the moment
it happens — it admits one person to a conversation that starts as soon as the
second player is in it — so a chat built later subscribes to these and grows its
roster rather than querying for a completed line-up. ``SeatLapsed`` is the
sweep's, and it is emphatically **not** ``SeatDeclined``: *answers challenges* is
a Strand over challenges that got an answer inside their window, and it is
unmeasurable if silence and a no are one event.

**One departure, written over an acceptance** (``docs/adr/0162``). ``SeatLeft``
is somebody leaving a game they had agreed to, which can only happen on a court
whose line-up had completed — so it is the one seat event the fold learns a
second fact from: *this challenge has been a game*, which no arrangement of the
seats can say once the departed's position has been given to somebody else. It
is not an answer to an invitation and the history walk does not count it as one.

**One re-seating.** ``SeatsInvited`` carries the **whole** resulting arrangement
rather than a delta, because completing a half-built line-up moves accepted
players across the net *and* fills the empty seats in one act; two events would
let a reader fold a half-applied court nobody built. It is safe to be one because
a send with nobody new is refused, so there is no rearrange-without-invite path
to represent — which is also where *once the court is full, the sides are frozen*
comes from.

**No ``GameOn``, no ``ChallengeDeclined``, no ``ChallengeExpired``.** A derived
standing has exactly one place to be true (``standing.py``), and an event
announcing a conclusion the fold already reaches would become the second — and it
would be the one that got believed.

**One withdrawal, and it is that rule's first and only exemption**
(``docs/adr/0142`` §3). ``ChallengeWithdrawn`` announces a conclusion, and it is
allowed to because **no arrangement of the seats reaches it**: every other
standing is a reading of the seats and the clock, and this one is a decision a
person took, with nothing in the seats to fold it out of. So the event is not a
second place for the fact to be true — it is the only place, and the fold reads
it exactly as it reads an acceptance. That is the whole of the test any future
candidate has to pass, and ``tests/unit/test_challenge_aggregate.py`` runs it
over this module rather than leaving it as prose.

**Every seating event carries the seats, and that is what makes the log
queryable.** A challenge's stream id is minted rather than derived from the
people in it, so *which challenges is this player in* cannot be a keyed read; it
matches the serialized seats, exactly as the Blocks context's exclusion read
matches its two player-id fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ChallengeSent:
    """One player's ask to play, sent to everybody on a built court at once.

    ``mode`` is the kind of evening the search was run for, and is ``None``
    exactly when the send came from a surface that has none — the deck, which
    deals one card at a time and asks nobody to pick a mode.

    ``window`` is the code derived from the grid **the search actually ran on**,
    stamped here and never re-derived. That grid does not survive the send, so
    recording the result is the only way to keep ADR-0100's promise that the
    window says what the person answering is agreeing to; re-deriving it on read
    would let the organiser silently change the proposal by editing their week,
    and a proposal that moves after it is sent is not a proposal.
    """

    challenge_id: UUID
    sport: str
    mode: str | None
    window: str
    organiser_id: UUID
    #: The whole court, in its fixed order: every seat's side, its occupant if it
    #: has one, and — for an invited seat — that seat's own deadline and the
    #: origin it was drawn from. See ``seats.py`` for the code.
    seats: tuple[str, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        _retuple(self, "seats")


@dataclass(frozen=True)
class ChallengeOpenedFromMutualInterest:
    """Two *Let's play* yeses that met. **Born accepted, with no deadline.**

    Asking the second player to accept a yes they had already given was the
    alternative; this exists because *that player has left the deck for good,
    because you now have an open game together* is true the moment the mutual is
    detected, and a challenge that had to be answered would make it not yet true.

    It carries **no mode and no window**: nobody picked a kind of evening and no
    grid was proposed from. The pair are seated in the court's first two
    positions, which puts them one per side in a singles sport and both on one
    side in a doubles one — half a game, with a side still to fill.

    ``organiser_id`` is the player whose yes closed the loop. Nothing about the
    standing turns on it while both seats are accepted; it is the seat the
    aggregate treats as the proposer's if the game is later completed.
    """

    challenge_id: UUID
    sport: str
    organiser_id: UUID
    other_player_id: UUID
    seats: tuple[str, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        _retuple(self, "seats")


@dataclass(frozen=True)
class SeatAccepted:
    """One person said yes. **Consequential on its own**, never a step to a total."""

    challenge_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SeatDeclined:
    """One person said no. It reopens **their** seat and disturbs nothing else.

    A judgement, and the reason this is a different event from ``SeatLapsed``
    rather than an outcome field on one.
    """

    challenge_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SeatLapsed:
    """One answer window passed with nothing in it.

    Recorded by the sweep, and it buys the **record** rather than correctness:
    every read is bounded by ``now``, so the seat already reads as lapsed whether
    or not anything swept it. What this event buys is a durable denominator for
    *answers challenges* the moment there is a context to count it.
    """

    challenge_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SeatLeft:
    """One person left a game they had agreed to. It reopens **their** seat.

    Written on an **accepted** seat of a challenge that is ``ON`` and on no
    other, which is what makes it carry a second fact for free: a court this was
    written on had become a game, and the fold keeps that (``game_opened``) so a
    court the organiser is left alone on is a game with a seat to fill rather
    than a send nobody answered.

    A decision and not a judgement about an invitation — it is kept apart from
    ``SeatDeclined`` for the same reason a lapse is, and it is **recorded and
    not yet scored** (``docs/adr/0162`` §8).
    """

    challenge_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class ChallengeWithdrawn:
    """The organiser ended a line-up nobody was going to complete.

    **The one event here that is not about a seat**, which is exactly what makes
    it the exemption rather than a breach: a fact about a seat is a fact the fold
    already has, and this one is not in the seats anywhere.

    It carries **no player**, and that is not an omission. Only the organiser may
    withdraw, the organiser's seat is on the stream from the opening event, and a
    second copy of *who* would be a second place for it to be true — the failure
    ``SeatLapsed`` avoids by carrying the one player a whole-court event could
    not otherwise name. Whole-challenge and irreversible: there is no
    ``ChallengeReopened`` beside this, because re-asking the same people is a
    **new** challenge with fresh deadlines and its own ``answered`` set.
    """

    challenge_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SeatsInvited:
    """The court as it now stands, and which of its seats are newly asked.

    The whole arrangement travels, because a completion does two things at once —
    an accepted player crosses the net *and* the empty seats fill — and one event
    is what stops a reader folding a half-applied court.

    ``newly_invited`` is stated rather than derived: *only the newly seated are
    invited* is the rule a notification path reads, and asking somebody twice
    reads as the platform having lost track of them.

    ``invited_by`` is the member who filled the seats, and it is **not the
    organiser**: ADR-0150 settled that *any live member may fill; only the
    organiser may withdraw*, so a reader that took the organiser would name the
    wrong person on a mutual-born doubles court. It is the only whole-court event
    here that names a player, which is ``ChallengeWithdrawn``'s argument in
    reverse — there the organiser is already on the stream, and here the filler
    may be anybody on it.

    **Nullable, and only for rows written before it existed** — which is also
    why this is an addition rather than a version 2, against the letter of this
    module's own docstring. Three things decide it and each is checkable.

    *The rule's reason survives.* ``.claude/rules/domain-events.md`` asks that
    *the rows already in the store must keep decoding*, and they do:
    ``_coerce_payload`` walks the **payload's** keys, so a row written before this
    field takes the default. Nothing stored is reinterpreted — a missing
    ``invited_by`` reads as *nobody knows who filled these seats*, which is the
    truth about those rows.

    *A version 2 here costs two classes and buys nothing.*
    ``EventCatalog.register`` binds one class to one ``(name, version)`` and
    raises on a second, so *version 2 beside version 1* is two Python classes and
    a fold with two branches for the life of the context — to express one
    nullable field that changes no existing row's meaning.

    *And the line that needs it could not be drawn otherwise.* The seats-invited
    system line renders ``{name}`` from ``actor_id``, ADR-0150 lets **any live
    member** fill, and the organiser is on the stream already — so taking the
    organiser would name the wrong person on exactly the mutual-born doubles
    court that record was written for.

    **The rule still binds where it was aimed.** A field whose absence would have
    to be *guessed at* rather than read as an honest nothing, or one that changes
    what a stored row means, is still a version 2 — and then it is worth its two
    classes.
    """

    challenge_id: UUID
    seats: tuple[str, ...]
    newly_invited: tuple[str, ...]
    occurred_at: datetime
    invited_by: UUID | None = None

    def __post_init__(self) -> None:
        _retuple(self, "seats", "newly_invited")


def _retuple(event: object, *fields: str) -> None:
    """Force a collection field to a tuple, on the way in and out of storage.

    The codec encodes a tuple as a JSON array and decodes it back as a ``list``,
    so without this an event that has been through the store is unequal to the
    event that was appended — and a replay would fold lists where the first pass
    folded tuples. Frozen dataclasses are assigned through ``object`` for the
    same reason ``__post_init__`` normalisation always is.
    """

    for field in fields:
        object.__setattr__(event, field, tuple(getattr(event, field)))
