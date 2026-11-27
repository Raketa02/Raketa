"""The Payments context's ports, in its own words.

The payment provider — the port onto the outside world — is in ``provider.py``,
and what it tells Rakieta unprompted is in ``notices.py``. What is here is what
this context keeps and what it asks of the rest of the platform.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant
from app.modules.payments.domain.club_payout import ClubPayout
from app.modules.payments.domain.payment_method import PaymentMethod
from app.modules.payments.domain.seat_charge import SeatCharge


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
    live yeses (proposals, #538) and booked games still ahead (bookings, #541).
    The yeses are answered by an adapter signed in ``proposals/infrastructure/``,
    so the arrow runs ``proposals → payments``; booked games are nought until a
    booking can hold one."""

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


@runtime_checkable
class ConnectedAccounts(Protocol):
    """**The clubs Rakieta sells for, by their accounts at the provider** — told
    when the provider says one changed (#537). A club is the seller, so its
    account is the Club context's to record; this context holds the provider
    and hears its notices, and passes this one on. Answered in
    ``payments/infrastructure/``, so the arrow runs ``payments → clubs``."""

    async def heed(self, account_id: str) -> bool:
        """The provider said this account changed: read it as it stands and
        record it on the club that holds it — in the caller's transaction,
        without committing. ``False`` for an account no club here opened."""
        ...


# --------------------------------------------------------------------------- #
# Seat charges (#541)
# --------------------------------------------------------------------------- #


@runtime_checkable
class SeatChargeRepository(Protocol):
    """One stream per charge, and the ``seat_charges`` projection written by
    ``save`` in the caller's transaction — what a notice finds its charge by,
    what a later fill finds a confirmed hold by, and what receipts read."""

    async def load(self, charge_id: UUID) -> SeatCharge | None: ...

    async def save(self, charge: SeatCharge) -> None:
        """Append what the charge recorded and write its row, in the caller's
        transaction."""
        ...

    async def of_game(self, game_id: UUID) -> Sequence[SeatCharge]:
        """Every charge ever made for this game, oldest first."""
        ...

    async def by_payment(self, payment_id: str) -> SeatCharge | None:
        """The charge whose payment at the provider this is — how a notice,
        which names a payment and never a player, finds its stream."""
        ...

    async def receipts_of(self, player_id: UUID) -> Sequence[SeatCharge]:
        """Every charge of this player's that is a receipt (#641): each one
        taken, or being taken, and each held for a booked game and let go
        untaken — **the latest taken first**."""
        ...

    async def games_held_until(self, moment: Instant) -> Sequence[UUID]:
        """Every game with a share still held for it to be taken at or before
        ``moment`` — its cut-off, or a holding's last safe moment (#639) — what
        the cut-off takes (#637), the earliest first."""
        ...

    async def games_to_hold_by(self, moment: Instant) -> Sequence[UUID]:
        """Every game with a share checked at its fill whose Holding time is at
        or before ``moment`` — what the holding holds (#639) — and every game
        with a share refused there for want of terms or a method, which the
        holding asks again once its player fixed them; the earliest first."""
        ...

    async def checked_of(
        self, player_id: UUID, game_ids: Collection[UUID]
    ) -> Mapping[UUID, Instant]:
        """This player's shares only checked for these games, each game's
        Holding time — *held from Sat 19:00* (#639)."""
        ...


@final
@dataclass(frozen=True, slots=True)
class Seller:
    """The club a share is paid to — the merchant of record, named on every
    receipt — its account at the provider, and where its desk is emailed (its
    one sign-in, #548): ``None`` for a club nobody signs in for."""

    name: str
    account_id: str | None
    email: str | None = None


@runtime_checkable
class Sellers(Protocol):
    """**A demand of the Club context**: what a club is called, and its account
    at the provider (#537). Answered over the Club courts stream, so the arrow
    runs ``payments → clubs``."""

    async def of(self, club_ids: Collection[UUID]) -> Mapping[UUID, Seller]:
        """Each of these clubs. A club that does not exist is absent."""
        ...


@final
@dataclass(frozen=True, slots=True)
class Payer:
    """Where a player's money emails go, and the nickname they are greeted by
    in them (``docs/adr/0199`` §1) — ``None`` for an account with none, which
    is greeted by nobody's name."""

    email: str
    nickname: str | None


@runtime_checkable
class Payers(Protocol):
    """**A demand of the users context**: each player's address and
    nickname."""

    async def of(self, player_ids: Collection[UUID]) -> Mapping[UUID, Payer]:
        """Each of these players. An account that no longer exists is absent."""
        ...


# --------------------------------------------------------------------------- #
# Club payouts (#548)
# --------------------------------------------------------------------------- #


@runtime_checkable
class ClubPayoutRepository(Protocol):
    """One stream per club per day it is paid for, and its projection —
    ``club_payouts``, and ``club_payout_games``, which holds each game paid out
    once — written by ``save`` in the caller's transaction."""

    async def load(self, payout_id: UUID) -> ClubPayout | None: ...

    async def save(self, payout: ClubPayout) -> None: ...

    async def owed(self, *, starting_before: Instant) -> Mapping[UUID, frozenset[UUID]]:
        """Each club's games starting before ``starting_before``, a share of
        which was taken, and which no payout has carried yet — **candidates**,
        not conclusions: whether a game is over and its money settled is asked
        of each."""
        ...

    async def paid_out(self, game_ids: Collection[UUID]) -> frozenset[UUID]:
        """Which of these games a payout the provider took has carried — on
        its way to the club's bank, or there."""
        ...


@runtime_checkable
class GamesOver(Protocol):
    """**A demand of the contexts that book games**: which games are over for
    good — played, or called off with what that gives back already decided — so
    that nothing can move their money any more (#548). Answered by
    ``proposals``, signed in ``proposals/infrastructure/``, so the arrow runs
    ``proposals → payments``."""

    async def over(self, game_ids: Collection[UUID], *, at: Instant) -> frozenset[UUID]:
        """Which of these games are over at ``at``. A game nobody booked is not."""
        ...
