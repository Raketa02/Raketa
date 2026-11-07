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

``PaymentsCheckedShares`` holds a share checked at its game's fill at its
Holding time, ``PaymentsCardsToFix`` keeps or lets go a refused holding, and
``PaymentsHoldingTimes`` says when a checked share is held (#639).

``PaymentsSeatRefunds`` gives a booked game's shares back — a share only held
let go, a share taken refunded (#544, #637) — ``PaymentsHeldShares`` is what the
cut-off takes (#637), and ``PaymentsLateRefunds`` says what a leaver after the
cut-off would get back if somebody took their seat: the share less exactly the
fee kept on their payment, never an estimate (#641).

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
from app.modules.payments.application.covers import (
    CourtToHold,
    HoldTheCourt,
    SettleTheCovers,
)
from app.modules.payments.application.refunds import (
    GiveTheSharesBack,
    TellTheLateLeaver,
)
from app.modules.payments.application.refunds import (
    RefundReason as PaymentsRefundReason,
)
from app.modules.payments.application.seat_charge_emails import CancelledBecause
from app.modules.payments.application.seat_charges import (
    ChargeTheSeats,
    ConfirmSeatCharge,
    HoldTheCheckedShares,
    KeepTheFixedShare,
    LetTheUnfixedShareGo,
    PaymentToConfirmOn,
    ReleaseCharges,
    TakeTheHeldShares,
)
from app.modules.payments.application.seat_charges import (
    GameToCharge as ChargedGame,
)
from app.modules.payments.domain.ports import (
    ClubPayoutRepository,
    Commitments,
    PaymentMethodRepository,
    SeatChargeRepository,
)
from app.modules.payments.domain.errors import SeatChargeNotFound
from app.modules.payments.domain.seat_charge import PAID, SeatChargeStatus
from app.modules.proposals.domain.errors import BookingNotFound
from app.modules.proposals.domain.club_bookings import (
    ClubStatus,
    Takings,
    club_status,
    known_sum,
)
from app.modules.proposals.domain.home import BookingStage, ClubCancelReason
from app.modules.proposals.domain.home import LateRefund, PayMode
from app.modules.proposals.domain.ports import (
    GameToCharge,
    Holding,
    PaymentRefusal,
    PlayerBookings,
    ProposalDirectory,
    RefundReason,
    RefusedPayment,
    SeatsCharged,
    SendersCourt,
    SendersCourtHeld,
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
                accepting=game.accepting,
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
class PaymentsSendersCourts:
    """``SendersCourts`` over the Payments context's own step (#751): the
    whole court on the sender's card at send — and, the send refused, the same
    answers recorded as nothing booked."""

    def __init__(self, hold: HoldTheCourt) -> None:
        self._hold = hold

    async def hold(
        self, court: SendersCourt, sender: UUID, *, at: Instant
    ) -> SendersCourtHeld:
        return await self._held(court, sender, at=at, books=True)

    async def refused(
        self, court: SendersCourt, sender: UUID, *, at: Instant
    ) -> SendersCourtHeld:
        return await self._held(court, sender, at=at, books=False)

    async def _held(
        self, court: SendersCourt, sender: UUID, *, at: Instant, books: bool
    ) -> SendersCourtHeld:
        try:
            held = await self._hold.execute(
                CourtToHold(
                    game_id=court.booking_id,
                    club_id=court.club_id,
                    sport=court.sport,
                    starts_at=court.start,
                    share_grosze=court.share_grosze,
                    court_name=court.court_name,
                    seats=court.seats,
                    whole_court=court.pay_mode is PayMode.WHOLE_COURT,
                    free_to_leave_until=court.free_to_leave_until,
                    covers_until=court.covers_until,
                ),
                sender,
                at=at,
                books=books,
            )
        except SeatChargeNotFound as theirs:
            # A booking id another sender's send was refused under.
            raise BookingNotFound() from theirs
        return SendersCourtHeld(
            refused=tuple(
                RefusedPayment(
                    seat_charge_id=seat.charge_id,
                    refusal=PaymentRefusal(seat.reason.value),
                )
                for seat in held.refused
            )
        )


@final
class PaymentsCoversAtTheCutOff:
    """``CoversAtTheCutOff`` over the Payments context's own step (#751)."""

    def __init__(self, settle: SettleTheCovers) -> None:
        self._settle = settle

    async def settle(self, booking_id: UUID, *, at: Instant) -> int:
        # A friends game's charges are made for its own id.
        return await self._settle.execute(booking_id, at=at)


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
    RefundReason.CALLED_OFF_BY_THE_SENDER: (
        PaymentsRefundReason.CALLED_OFF_BY_THE_SENDER
    ),
}


@final
class PaymentsSeatRefunds:
    def __init__(
        self, refund: GiveTheSharesBack, *, late_leaver: TellTheLateLeaver
    ) -> None:
        self._refund = refund
        self._late_leaver = late_leaver

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

    async def seat_taken(
        self, booking_id: UUID, payer: UUID, *, cover: bool, at: Instant
    ) -> None:
        await self._refund.one_seat(booking_id, payer, cover=cover, at=at)

    async def left_after_the_cut_off(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> None:
        # A booking takes its proposal's id, which every charge was made for.
        await self._late_leaver.execute(booking_id, player_id, at=at)


@final
class PaymentsHeldShares:
    def __init__(self, take: TakeTheHeldShares) -> None:
        self._take = take

    async def due(self, *, at: Instant) -> Sequence[UUID]:
        return await self._take.due(at=at)

    async def take(self, booking_id: UUID, *, at: Instant) -> int:
        # A booking takes its proposal's id, which every charge was made for.
        return await self._take.execute(booking_id, at=at)


@final
class PaymentsCheckedShares:
    def __init__(self, hold: HoldTheCheckedShares) -> None:
        self._hold = hold

    async def due(self, *, at: Instant) -> Sequence[UUID]:
        return await self._hold.due(at=at)

    async def hold(
        self,
        booking_id: UUID,
        *,
        fix_by: Instant,
        fixing_until: Mapping[UUID, Instant],
        at: Instant,
    ) -> Holding:
        # A booking takes its proposal's id, which every charge was made for.
        holding = await self._hold.execute(
            booking_id, fix_by=fix_by, fixing_until=fixing_until, at=at
        )
        return Holding(
            held=holding.held,
            refused={
                player: RefusedPayment(
                    seat_charge_id=seat.charge_id,
                    refusal=PaymentRefusal(seat.reason.value),
                )
                for player, seat in holding.refused.items()
            },
        )


@final
class PaymentsCardsToFix:
    def __init__(
        self, *, keep: KeepTheFixedShare, let_go: LetTheUnfixedShareGo
    ) -> None:
        self._keep = keep
        self._let_go = let_go

    async def keep_fixed(self, seat_charge_id: UUID, *, at: Instant) -> bool:
        return await self._keep.execute(seat_charge_id, at=at)

    async def let_go_unfixed(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> None:
        # A booking takes its proposal's id, which every charge was made for.
        await self._let_go.execute(booking_id, player_id, at=at)


@final
class PaymentsHoldingTimes:
    def __init__(self, charges: SeatChargeRepository) -> None:
        self._charges = charges

    async def of(
        self, player_id: UUID, booking_ids: Collection[UUID]
    ) -> Mapping[UUID, Instant]:
        # A booking takes its proposal's id, which every charge was made for.
        return await self._charges.checked_of(player_id, booking_ids)


@final
class PaymentsBookingTakings:
    """``BookingTakings`` over each booking's Seat charges (#547): what was
    taken — a share being captured or captured; **never a share only held**,
    which is listed as held and collects nothing (#637) — and what was given
    back, at what the provider gave or, until it answers, what was decided; the
    card fees and what is the club's, and whether a payout carried it (#548).
    **Never an estimate** (#641): a fee the provider has not said yet leaves
    the card fees — and a refund less it, and the net — not yet known."""

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
            charges = await self._charges.of_game(booking_id)
            paid = [charge for charge in charges if charge.status in PAID]
            held = frozenset(
                charge.player_id
                for charge in charges
                if charge.status is SeatChargeStatus.HELD
            )
            if paid or held:
                takings[booking_id] = Takings(
                    paid=frozenset(charge.player_id for charge in paid),
                    collected_grosze=sum(charge.amount_grosze for charge in paid),
                    refunded_grosze=known_sum(
                        charge.given_back_grosze for charge in paid
                    ),
                    card_fees_grosze=known_sum(
                        charge.card_fee_grosze for charge in paid
                    ),
                    paid_out=booking_id in paid_out,
                    held=held,
                )
        return takings


@final
class PaymentsLateRefunds:
    def __init__(self, charges: SeatChargeRepository) -> None:
        self._charges = charges

    async def of(self, booking_id: UUID, player_id: UUID) -> LateRefund | None:
        # A booking takes its proposal's id, which every charge was made for;
        # a player pays one share of a game at most — a friends game's sender
        # his covers too, which are no seat of his to leave (#752).
        taken = [
            charge
            for charge in await self._charges.of_game(booking_id)
            if charge.player_id == player_id
            and charge.status in PAID
            and not charge.cover
        ]
        if not taken:
            return None
        back, fee = taken[-1].less_the_fee_kept_grosze, taken[-1].fee_kept_grosze
        if back is None or fee is None:
            return None
        return LateRefund(refund_grosze=back, fee_kept_grosze=fee)


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
            if game is None:
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
