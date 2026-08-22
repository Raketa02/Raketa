"""A scheduled look at one match, and the name it is done under.

ADR-0076 and ``Raketa02/Raketa#72``. **A wake is a look, not an instruction** —
it carries no verb, and the handler re-derives everything from the record it
finds. What this value carries is only enough to say *which* look: the match,
the threshold that was ahead when the schedule was last armed, and the moment it
was armed for.

**The reason travels with it and nothing branches on it.** It was computed at a
past write, and the match may have moved since — a seat paid, a club cancelled,
a player left. A handler acting on it would write a stale intention into the
record, and that is the failure ADR-0076 spends a section refusing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Instant, WakeReason


@final
@dataclass(frozen=True)
class MatchWake:
    """One match, one threshold, one moment."""

    match_id: UUID
    reason: WakeReason
    scheduled_for: Instant

    @property
    def key(self) -> str:
        """``{matchId}:{threshold}:{scheduledFor}`` — ADR-0076's idempotency key.

        **What makes taking it twice safe is not this string.** Safety comes
        from the look being a look: the second one re-derives from a record the
        first already moved, finds nothing left to do, and writes nothing. That
        is why ADR-0076 can promise at-least-once delivery with *"no exactly-once
        guarantee, no leader election and no distributed lock"* — and why there
        is no table of handled keys anywhere. **The record's own schedule column
        is the ledger of which wakes are outstanding**, because a look that acts
        re-arms it to a strictly later moment.

        So the key names the look rather than guarding it: it is what a log line
        and a support question are keyed on, and it is the reason `wake_reason`
        is stored at all.
        """

        return f"{self.match_id}:{self.reason.value}:{self.scheduled_for.isoformat()}"
