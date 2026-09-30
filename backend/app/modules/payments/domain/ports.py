"""The Payments context's ports, in its own words.

The payment provider — the port onto the outside world — is in ``provider.py``,
and what it tells Raketa unprompted is in ``notices.py``. What is here is what
this context keeps and what it asks of the rest of the platform.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant
from app.modules.payments.domain.payment_method import PaymentMethod


@runtime_checkable
class PaymentMethodRepository(Protocol):
    """One stream per player. ``load`` answers an unwritten aggregate rather than
    ``None``: a player who never opened the setup has no method, and every act
    starts from there."""

    async def load(self, player_id: UUID) -> PaymentMethod: ...

    async def save(self, payment_method: PaymentMethod) -> None:
        """Append what the aggregate recorded, in the caller's transaction."""
        ...

    async def player_of_customer(self, customer_id: str) -> UUID | None:
        """Whose customer this is at the provider — how a notice about a
        customer finds its stream. ``None`` for a customer nobody here opened."""
        ...


@final
@dataclass(frozen=True, slots=True)
class Commitments:
    """What could still be charged to a player's method: yeses on games still
    filling, and booked games not yet played."""

    live_yeses: int
    upcoming_games: int

    @property
    def any(self) -> bool:
        return self.live_yeses > 0 or self.upcoming_games > 0


@runtime_checkable
class PaymentCommitments(Protocol):
    """**A demand of the contexts that make games**, answered by them: a player's
    live yeses (proposals, #540) and booked games still ahead (bookings, #541).
    Neither exists yet, so one adapter answers nothing (``NoCommitmentsYet``) —
    and *remove* is refused from the day either does, with no change here."""

    async def of(self, player_id: UUID, *, at: Instant) -> Commitments: ...


@runtime_checkable
class NoticeInbox(Protocol):
    """Which provider notices were already read — the webhook's own
    deduplication, by the notice's id."""

    async def first_reading(self, notice_id: str, *, kind: str, at: Instant) -> bool:
        """Record the notice as read, in the caller's transaction, and answer
        whether this is the first time. A notice read before answers ``False``
        and records nothing."""
        ...
