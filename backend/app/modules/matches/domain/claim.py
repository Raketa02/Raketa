"""A player's exclusive right to buy one seat, for five minutes.

ADR-0081. **A seat claim is not a seat state.** The glossary spells a seat three
ways — *paid · held · empty* — where **held** means a name on a seat and no
money, an invitation living for hours and given to a player by a person. A
payment window is minutes long and taken by the taker, so widening `held` would
put a payer's level into a match's forecast for five minutes and take it out
again when their card declines; and a fourth seat state would grow a branch in
the fill count, the forecast, the hold ladder and the card's copy at once. So
this is its own short-lived record, and the seat below it is untouched: still
empty, still absent from the fill count, still doing nothing for the hold
ladder.

The glossary sentence survives word for word — *"there is no window in which a
seat is taken and unpaid by the taker"* — because nobody has taken a seat. They
have taken the place in the queue in front of it.

**Live is composed, never latched.** A claim whose five minutes have run out is
over at the instant they ran out, whether or not any wake has written the
receipt yet, and `is_live` asks the kernel rather than answering itself. That is
the same shape as a stale court hold and it matters for the same reason: nothing
downstream may depend on the reaper having got there first, because the reaper is
a scheduled look and the player is a tap.

**One rule ends a claim, whatever ended it** (ADR-0081), so there is exactly one
mutator. The five minutes running out, the seat being bought, and the match dying
underneath it are the same operation with different callers — and it is the
caller that announces, because a support agent needs to know which of the three
happened and the record deliberately does not say.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Instant, claim_is_live
from app.kernel import SeatClaim as RecordSeatClaim

from app.modules.matches.domain.errors import SeatClaimAlreadyEnded


@final
@dataclass
class SeatClaim:
    """One claim: which seat, whose, until when, and whether it is over.

    ``expires_at`` is stored rather than recomputed from ``claimed_at``. It is
    the fact the whole record exists to carry — the match's schedule is armed
    against it, and a client counts down to it — and recomputing it from a
    duration would mean a change to that duration silently rewrote the deadline
    of every claim already running.
    """

    id: UUID
    seat_index: int
    player_id: UUID
    claimed_at: Instant
    expires_at: Instant
    ended_at: Instant | None = None

    def __post_init__(self) -> None:
        if self.expires_at <= self.claimed_at:
            raise ValueError(
                f"a claim on seat {self.seat_index} that expires before it began"
            )

    @property
    def is_ended(self) -> bool:
        """Whether a receipt has been written. **Not the same as being over.**"""

        return self.ended_at is not None

    def is_live(self, at: Instant) -> bool:
        """Whether this is still the right to buy its seat, at that instant.

        Asks ``kernel.claim_is_live`` for the comparison rather than making it
        here: the strictness is load-bearing — a claim expiring exactly at the
        moment a wake is armed for must read as *over*, or the look finds it
        running and re-arms itself where it stands for ever.
        """

        return not self.is_ended and claim_is_live(self.as_record(), at)

    def end(self, *, at: Instant) -> bool:
        """Close it, at `at` or at its own expiry — whichever came first.

        **The `min` is the whole of *one rule ends a claim*.** A reaper arriving
        late must date the lapse when the five minutes actually ran out and not
        when it noticed, because the thirty-second cooldown is measured from
        here and a downed worker would otherwise extend it by however long it
        was down. A redemption and a match dying underneath both land strictly
        before the expiry and take `at` unchanged.

        Refused rather than ignored on a claim that has already ended: moving
        the instant a claim closed is history rewritten rather than recorded,
        the same argument that refuses a vacancy being filled twice.
        """

        if self.ended_at is not None:
            raise SeatClaimAlreadyEnded()
        self.ended_at = min(at, self.expires_at)
        return True

    def as_record(self) -> RecordSeatClaim:
        """The two facts the wake function reads. **No player identity crosses.**"""

        return RecordSeatClaim(
            seat_index=self.seat_index, expires_at=self.expires_at
        )
