"""What a caller asks the Matches context to do.

**No command carries a court.** A match asks Courts for *a category and a
window* and is given a reservation or refused (ADR-0035), so which court it ends
up on is never a caller's input and never a match's fact.

**No command carries a version.** ADR-0074 refused a version on the wire and the
same argument holds inside: the guard is the repository's, taken on the row it
is writing, and a version threaded through a command is one a caller can hold
stale and re-send. A losing writer reloads.

**Nothing says when it was issued.** The instant of a write comes from the
``Clock`` port, so a caller cannot post a match into last week by asserting it.
``start`` is the exception and is not one: it is *when the match is played*,
which is the thing being asked for.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from app.kernel import (
    Instant,
    MatchKind,
    Minutes,
    Outcome,
    PayModel,
    SeatShare,
    Sport,
)

from app.modules.matches.domain.score import Score


class CancellationCause(str, Enum):
    """The four cancellations, and they are four different stories.

    ``CLUB`` and ``WEATHER`` are **Declarations** — no reader can derive that a
    manager or the weather decided something. ``INCOMPLETE`` and ``CHECKPOINT``
    are **receipts** on conclusions the clock already reached, and writing one
    records only that the refund, the court release and the notice completed
    (ADR-0034). Naming them in one enum is not naming them one thing: the use
    case fans out to four different aggregate methods and four different
    announcements.
    """

    CLUB = "club"
    WEATHER = "weather"
    INCOMPLETE = "incomplete"
    CHECKPOINT = "checkpoint"


@dataclass(frozen=True)
class PostMatchCommand:
    """*This sport, at this club, at this hour, at this price a seat.*"""

    club_id: UUID
    category_id: UUID
    sport: Sport
    start: Instant
    duration: Minutes
    share: SeatShare
    counted: bool = True
    kind: MatchKind = MatchKind.OPEN
    pay_model: PayModel = PayModel.SPLIT
    open_seats: int = 0


@dataclass(frozen=True)
class MoveMatchStartCommand:
    """*The same match, at a different hour* (ADR-0032)."""

    match_id: UUID
    start: Instant


@dataclass(frozen=True)
class TakeSeatCommand:
    """*This player is in.* Which seat is the match's answer, not the caller's."""

    match_id: UUID
    player_id: UUID


@dataclass(frozen=True)
class ClaimSeatCommand:
    """*This player is buying a seat here* — the tap, not the money.

    **No seat.** Which one she gets is the match's answer, exactly as it is for
    ``TakeSeatCommand``: a caller that could name a seat could name one somebody
    else is already buying, and *which seat* is not a fact any screen is
    developed against.

    **No idempotency key**, and that is a decision rather than an omission. A
    replayed tap inside the five minutes finds her own live claim and is refused
    by name, which is the honest answer — she *is* already buying a seat. What
    an idempotency key would add is returning the first claim silently, and that
    would make a double tap indistinguishable from a genuine second attempt.
    """

    match_id: UUID
    player_id: UUID


@dataclass(frozen=True)
class RedeemSeatClaimCommand:
    """*The money landed; the seat she was buying is hers.*

    One command for both halves, because they are one moment: a redeemed claim
    takes the seat **and** pays for it, and a version of this that only took it
    would produce the taken-and-unpaid window the whole record exists to
    prevent.

    Where the money went is Money's (``Raketa02/Raketa#69``), and the
    transaction that joins this to the court it earns is ``#70``.
    """

    match_id: UUID
    player_id: UUID


@dataclass(frozen=True)
class PaySeatCommand:
    """*The money for this player's seat landed.*

    Recording it is this context's half. Where the money went is Money's
    (``Raketa02/Raketa#69``), and the transaction that joins the two to a court
    is ``Raketa02/Raketa#70``.
    """

    match_id: UUID
    player_id: UUID


@dataclass(frozen=True)
class DepartCommand:
    """*This player is out*, and this is the outcome she was looking at.

    **The quote is the one field a caller adds, and it is a label rather than an
    amount** (ADR-0033). An amount moves for reasons that have nothing to do
    with leaving — a discount landing, a club price change — and refusing on
    those is noise; the label is what she was actually shown as the basis for
    deciding. A strictly worse outcome at apply time is refused and she is
    re-presented.

    **It carries no amount and no outcome to settle at.** What she recovers is
    the departure's own answer on an axis of its own, and a caller that could
    state it would be the welding ADR-0033 exists to undo.

    *The client generates an idempotency key and sends it too (ADR-0086); the
    command log that consumes it is the route's* (``Raketa02/Raketa#80``)*, not
    this context's, so nothing here holds one.*
    """

    match_id: UUID
    player_id: UUID
    quote: Outcome


@dataclass(frozen=True)
class CancelMatchCommand:
    """*This match is not happening*, and which of the four stories it is.

    Four flags rather than one, because *"they are four different stories and
    the player deserves to know which one happened"* — and the record being the
    explanation is what lets Matches keep no history at all.
    """

    match_id: UUID
    cause: CancellationCause


@dataclass(frozen=True)
class ResolveCourtHoldCommand:
    """*Look at this match's court and do what the ladder says.*

    One field, and it carries no reason: a wake is a look and the handler
    re-derives (ADR-0076, ``Raketa02/Raketa#72``). A command naming the threshold
    it thinks was crossed would let a late look act on a fact that has since
    stopped being true.
    """

    match_id: UUID


@dataclass(frozen=True)
class ProposeScoreCommand:
    """*This is what we played.* The route that asks is ``Raketa02/Raketa#79``."""

    match_id: UUID
    player_id: UUID
    score: Score


@dataclass(frozen=True)
class AgreeResultCommand:
    """*That is the score* — or nobody answered for twenty-four hours."""

    match_id: UUID
    by_silence: bool = False
