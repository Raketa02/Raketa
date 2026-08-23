"""The command log ADR-0030 requires of every destructive command.

*"We will give destructive commands a command log keyed ``(command, idempotency
key)`` with a 24-hour expiry, rather than keeping an idempotency key on an
emptied seat or answering a replay from the departure record."*

Both alternatives it names are the same mistake in two places: an emptied seat
has nothing left to hold a key on, and the departure record answers *whose money
is this* rather than *did I already do this*. So the log is its own table and its
own port, cross-cutting like the unit of work beside it — the second destructive
command to arrive gets a home rather than a precedent to copy.

**Why a key at all, when the write is nearly idempotent by nature.** A replayed
departure would be refused by the aggregate (she holds no seat), and ADR-0070's
*a refusal is not a second shape* would turn that into a perfectly good screen.
What it could not do is answer **what she was quoted the first time** — and that
is the one thing the second tap is asking about.

**24 hours**, because the failure it guards is HTTP-retry-scale rather than
outbox-scale. Expiry is observed on the **read**: a row older than the window is
not a replay, whether or not anything has pruned it yet. Pruning is the
adapter's, and it happens on the write, so the table cannot grow without a
scheduler nobody has built.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant
from app.shared.domain.errors import ConflictError

#: How long a key answers for the command it was first sent with (ADR-0030).
COMMAND_LOG_WINDOW_HOURS = 24


class IdempotencyKeyIsAnothers(ConflictError):
    """This key has already answered for a different player's command.

    ADR-0030 keys the log ``(command, idempotency key)`` and the key is the
    **client's** to choose, so two clients can choose one. Storing the player
    beside the row and refusing a mismatch is what stops the second player being
    handed the first one's outcome — and refusing is strictly safer than the
    alternative of folding the player into the key, which would quietly *apply*
    the second command instead of noticing the collision.

    It lives here rather than with any one command, for the same reason the log
    does: the second destructive command to arrive will make the same mistake
    and needs the same refusal. It is also a genuine conflict rather than a
    refusal of the act — nothing about the match is wrong, and re-sending with a
    fresh key succeeds.
    """

    code = "command_key_belongs_to_another"

    def __init__(self) -> None:
        super().__init__("That request key has already been used by somebody else.")


@final
@dataclass(frozen=True)
class LoggedCommand:
    """One destructive command that has already been applied once.

    ``result`` is a short label naming **what happened**, not what was asked
    for: a departure applies at the outcome the aggregate recomputed, which is
    equal to or better than the quote that crossed the wire, and a replay must
    hand back the outcome she actually got.

    ``player_id`` is stored although the key does not include it. ADR-0030 fixes
    the key as ``(command, idempotency key)``, and a client's key is its own to
    choose — so the one thing that must never happen is one player's key
    answering for another's. The lookup returns the row and the caller refuses a
    mismatch; folding the player into the key would silently *apply* the second
    command instead, which is the failure the log exists to prevent.
    """

    command: str
    key: str
    player_id: UUID
    result: str
    recorded_at: Instant


@runtime_checkable
class CommandLog(Protocol):
    """What has already been done, under the key the client chose for it."""

    async def recall(
        self, *, command: str, key: str, now: Instant
    ) -> LoggedCommand | None:
        """The first application under this key, if it is still inside 24 hours.

        ``now`` crosses because the window is a **domain** rule and the adapter
        holds no clock — the same reason every other read in this app is handed
        an instant rather than reaching for one.
        """
        ...

    async def remember(self, entry: LoggedCommand) -> None:
        """Record an application, **without committing**.

        It joins the transaction its command is written in, or the log and the
        write it describes can disagree — which is the one state that makes a
        replay dangerous rather than merely useless.
        """
        ...
