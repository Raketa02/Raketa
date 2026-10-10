"""What passes between proposals and payments, every adapter **signed here**
so the arrow runs ``proposals → payments`` only.

``PaymentsSavedMethods`` answers this context's demand — *does this player have
a method to charge* — off the player's Payment method stream. A method whose
card moved brand is still a method: its terms are asked again before the fill
can charge it (the mechanics §19), and that is the fill's to meet, not a yes's.

``PaymentsSeatCharges`` and ``PaymentsUndecidedCharges`` are the fill's (#541):
every seat's share all or nothing, a refused payment its player confirmed, and
the charges a game will not be paid with let go — over the Payments context's
own use cases, its refusals translated into this context's words.

``PaymentsSeatRefunds`` gives a booked game's paid shares back — a leaver's
before the cut-off, less the card fee, and everybody's still in on a game
called off at its cut-off, in full (#544) — and ``PaymentsCardFees`` says what
the card fee on a share comes to, the estimate the leaving sheet quotes.

``BookedGamesOver`` answers **payments'** demand — *which games are over for
good*, so their money is the club's to be paid out (#548) — off the bookings as
this context reads them.

``LiveYesCommitments`` answers **payments'** demand — *could anything still be
charged to this method* — with the player's live yeses, across pools and sports,
and their booked games still ahead (the mechanics §12.4: *Remove only with
nothing live and no upcoming booked games*).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.bookings.domain.ports import BookingDirectory
from app.modules.payments.application.refunds import RefundTheSeats
from app.modules.payments.application.refunds import (
    RefundReason as PaymentsRefundReason,
)
from app.modules.payments.application.seat_charge_emails import CancelledBecause
from app.modules.payments.application.seat_charges import (
    ChargeTheSeats,
    ConfirmSeatCharge,
    PaymentToConfirmOn,
    ReleaseCharges,
)
from app.modules.payments.domain.card_fee import estimated_card_fee
from app.modules.payments.application.seat_charges import (
    GameToCharge as ChargedGame,
)
from app.modules.payments.domain.ports import (
    ClubPayoutRepository,
    Commitments,
    PaymentMethodRepository,
    SeatChargeRepository,
)
from app.modules.payments.domain.seat_charge import PAID
from app.modules.proposals.domain.club_bookings import (
    ClubStatus,
    Takings,
    club_status,
)
from app.modules.proposals.domain.home import BookingStage, ClubCancelReason
from app.modules.proposals.domain.ports import (
    GameToCharge,
    PaymentRefusal,
    PlayerBookings,
    ProposalDirectory,
    RefundReason,
    RefusedPayment,
    SeatsCharged,
)


@final
class PaymentsSavedMethods:
    def __init__(self, methods: PaymentMethodRepository) -> None:
        self._methods = methods

    async def saved_for(self, player_id: UUID) -> bool:
        return (await self._methods.load(player_id)).method is not None


@final
class PaymentsSeatCharges:
    def __init__(
        self,
        *,
        charge: ChargeTheSeats,
        confirm: ConfirmSeatCharge,
        to_confirm: PaymentToConfirmOn,
    ) -> None:
        self._charge = charge
        self._confirm = confirm
        self._to_confirm = to_confirm

    async def charge(
        self,
        game: GameToCharge,
        players: Sequence[UUID],
        *,
        attempt: int,
        at: Instant,
    ) -> SeatsCharged:
        charged = await self._charge.execute(
            ChargedGame(
                game_id=game.proposal_id,
                club_id=game.club_id,
                sport=game.sport,
                starts_at=game.start,
                share_grosze=game.share_grosze,
                court_name=game.court_name,
                free_to_leave_until=game.free_to_leave_until,
                rescue=game.rescue,
                pay_by=game.pay_by,
                paying_until=game.paying_until,
                booked_on_a_payment=game.booked_on_a_payment,
                filled_by=game.filled_by,
            ),
            players,
            attempt=attempt,
            at=at,
        )
        return SeatsCharged(
            taken=charged.taken,
            refused={
                player: RefusedPayment(
                    seat_charge_id=seat.charge_id,
                    refusal=PaymentRefusal(seat.reason.value),
                )
                for player, seat in charged.refused.items()
            },
        )

    async def confirmed(
        self, seat_charge_id: UUID, *, player_id: UUID, at: Instant
    ) -> UUID:
        confirmed = await self._confirm.execute(
            seat_charge_id, player_id=player_id, at=at
        )
        return confirmed.game_id

    async def to_confirm(self, game_id: UUID, *, player_id: UUID) -> UUID | None:
        return await self._to_confirm.execute(game_id, player_id=player_id)


@final
class PaymentsUndecidedCharges:
    def __init__(self, release: ReleaseCharges) -> None:
        self._release = release

    async def release(
        self,
        proposal_id: UUID,
        *,
        keeping: Collection[UUID],
        of_player: UUID | None = None,
        at: Instant,
    ) -> None:
        await self._release.execute(
            proposal_id, keeping=keeping, of_player=of_player, at=at
        )


_REASONS = {
    RefundReason.LEFT_BEFORE_THE_CUT_OFF: PaymentsRefundReason.LEFT,
    RefundReason.CALLED_OFF_AT_THE_CUT_OFF: (
        PaymentsRefundReason.CALLED_OFF_AT_THE_CUT_OFF
    ),
    RefundReason.SEAT_TAKEN: PaymentsRefundReason.SEAT_TAKEN,
    RefundReason.CANCELLED_BY_THE_CLUB: PaymentsRefundReason.CANCELLED_BY_THE_CLUB,
    RefundReason.CANCELLED_AFTER_YOU_LEFT: (
        PaymentsRefundReason.CANCELLED_AFTER_YOU_LEFT
    ),
}


@final
class PaymentsSeatRefunds:
    def __init__(self, refund: RefundTheSeats) -> None:
        self._refund = refund

    async def refund(
        self,
        booking_id: UUID,
        players: Collection[UUID],
        *,
        reason: RefundReason,
        at: Instant,
        because: ClubCancelReason | None = None,
    ) -> None:
        # A booking takes its proposal's id, which every charge was made for.
        await self._refund.execute(
            booking_id,
            players,
            reason=_REASONS[reason],
            at=at,
            because=None if because is None else CancelledBecause(because.value),
        )


@final
class PaymentsBookingTakings:
    """``BookingTakings`` over each booking's Seat charges (#547): what was
    taken — a share being captured or captured — and what was given back, at
    what the provider gave or, until it answers, what was decided; the card
    fees and what is the club's, and whether a payout carried it (#548)."""

    def __init__(
        self, charges: SeatChargeRepository, payouts: ClubPayoutRepository
    ) -> None:
        self._charges = charges
        self._payouts = payouts

    async def of(self, booking_ids: Collection[UUID]) -> Mapping[UUID, Takings]:
        takings: dict[UUID, Takings] = {}
        paid_out = await self._payouts.paid_out(set(booking_ids))
        for booking_id in sorted(set(booking_ids)):
            # A booking takes its proposal's id, which every charge was made for.
            paid = [
                charge
                for charge in await self._charges.of_game(booking_id)
                if charge.status in PAID
            ]
            if paid:
                takings[booking_id] = Takings(
                    paid=frozenset(charge.player_id for charge in paid),
                    collected_grosze=sum(charge.amount_grosze for charge in paid),
                    refunded_grosze=sum(charge.given_back_grosze for charge in paid),
                    card_fees_grosze=sum(charge.card_fee_grosze for charge in paid),
                    paid_out=booking_id in paid_out,
                )
        return takings


@final
class PaymentsCardFees:
    def card_fee_on(self, share_grosze: int) -> int:
        return estimated_card_fee(share_grosze)


@final
class BookedGamesOver:
    """Payments' ``GamesOver``: a game is over once it is **played** — its hour
    ended, and it was not called off — or **called off and recorded so**, in
    the act that decided what it gives back. A game read as called off only off
    the clock — short at its cut-off before the cut-off job reaches it — is not
    over yet: its refunds are still to be decided."""

    def __init__(self, bookings: PlayerBookings) -> None:
        self._bookings = bookings

    async def over(self, game_ids: Collection[UUID], *, at: Instant) -> frozenset[UUID]:
        over: set[UUID] = set()
        for game_id in sorted(set(game_ids)):
            # A booking takes its proposal's id, which every charge was made for.
            game = await self._bookings.find(game_id)
            # A game gone back to filling took no money (#624).
            if game is None or game.filling_again:
                continue
            if (
                game.stage is BookingStage.CALLED_OFF
                or club_status(game, now=at) is ClubStatus.PLAYED
            ):
                over.add(game_id)
        return frozenset(over)


@final
class LiveYesCommitments:
    def __init__(
        self, *, directory: ProposalDirectory, bookings: BookingDirectory
    ) -> None:
        self._directory = directory
        self._bookings = bookings

    async def of(self, player_id: UUID, *, at: Instant) -> Commitments:
        live = await self._directory.live_yeses_of(player_id, now=at)
        ahead = await self._bookings.starts_for(player_id, start=at, end=None)
        return Commitments(live_yeses=len(live), upcoming_games=len(ahead))
