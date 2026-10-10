"""Charging a game's seats, **all or nothing** (the mechanics §11–§12.2;
``docs/adr/0189`` §4; the mechanics Appendix A, *The fill*).

**Every seat is held first, on the club's account, off-session** — the player's
saved card cloned onto the seller's account for that one payment, authorised
with manual capture. Only when **every** seat is held is any taken; when one is
not, every hold is let go and **nobody pays**. A hold let go costs nothing.

**The holds are asked inline, because their answer is the response** — *It's a
game!* or *your payment didn't go through* — and before anything is written
(``docs/adr/0190`` §4). What is written is the verdict: every charge **taken**
with the booking, or the refused ones recorded and the others **released**.
The capture and the cancellation at the provider follow the commit, from the
outbox (``handlers/settle_seat_charges.py``), so a crash between the verdict and
the money leaves a decision a subscriber retries rather than money moved with
nothing written.

**A key is the game, the player, the attempt and the hour.** The attempt is the
caller's — the game's own record of how many times it has tried to fill — so a
request retried after an outage asks for the same holds again and the provider
answers the first ones, while the next attempt after a refusal asks afresh. The
hour bounds an outage the provider stored against a key (``docs/adr/0190`` §4).
A hold made and then orphaned by a transaction that never committed is not
cancelled by anybody: the next attempt in the hour is answered it again, and
otherwise the provider lets it lapse untaken, which costs nothing.

**A hold the player confirmed in the app is taken rather than asked for again**
— their bank may check every payment, and that is the one it gave — when the
fill it confirmed for books. When another seat is refused instead, it is let go
with every other hold: *if any fails, the others are cancelled* — **unless the
refused player is given time to pay** (#625, #626; the mechanics §12.2, Q109):
then every other hold is **kept** on its card, the new ones recorded held, so
that paying in time books the game on them and nobody's bank is asked again.

**Nothing here commits**: the fill's transaction is the caller's.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import final
from uuid import UUID

from app.application.ports import MailQueue
from app.kernel import Instant, Sport, invariant
from app.modules.payments.application.seat_charge_emails import (
    confirm_payment_email,
    game_booked_email,
)
from app.modules.payments.application.setup import key_hour
from app.modules.payments.domain.card_fee import estimated_card_fee
from app.modules.payments.domain.errors import (
    PaymentNotConfirmed,
    SeatChargeNotFound,
)
from app.modules.payments.domain.ports import (
    Payers,
    PaymentMethodRepository,
    SeatChargeRepository,
    Seller,
    Sellers,
)
from app.modules.payments.domain.provider import (
    Payment,
    PaymentProvider,
    PaymentStatus,
)
from app.modules.payments.domain.seat_charge import (
    PAID,
    FailureReason,
    SeatCharge,
    SeatChargeStatus,
)
from app.shared.ids import new_uuid


@final
@dataclass(frozen=True, slots=True)
class GameToCharge:
    """The game whose seats are charged, as the fill knows it."""

    #: The proposal that filled — the id its booking takes.
    game_id: UUID
    club_id: UUID
    sport: Sport
    starts_at: Instant
    share_grosze: int
    #: The court it is booked on, for the confirmation.
    court_name: str
    #: The club's cut-off, or ``None`` when the game filled after it.
    free_to_leave_until: Instant | None
    #: A seat a leaver left open on a booked game, taken by one player (#545)
    #: — its holds are keyed apart from the fill's, and a refusal asks them to
    #: confirm the payment to **take** the seat rather than to keep one.
    rescue: bool = False
    #: **Time to pay** (#625, #626): a refused share's seat is held for its
    #: player until then, and every other hold is kept for it — the email
    #: names the time. ``None`` lets every hold go: a rescue's refusal, and one
    #: with no time left before the book-by.
    pay_by: Instant | None = None
    #: The players already given time to pay, and when it ends: refused
    #: again, they keep it — and their email names it.
    paying_until: Mapping[UUID, Instant] = field(default_factory=dict)
    #: The game books on a payment it waited for (#625): the players were told
    #: *It's a game!* when it filled, so the receipt says *booked · you paid*
    #: (Q110) — but to the player whose payment booked it (``filled_by``), who
    #: sees *It's a game!* on their phone.
    booked_on_a_payment: bool = False
    filled_by: UUID | None = None


@final
@dataclass(frozen=True, slots=True)
class RefusedSeat:
    """A seat whose share could not be held, and the charge that says so."""

    charge_id: UUID
    reason: FailureReason


@final
@dataclass(frozen=True, slots=True)
class SeatsCharged:
    """Every seat taken — ``refused`` is empty — or nobody: ``refused`` names
    whose share could not be held, and nothing was taken."""

    #: Each player's charge, when every seat was taken.
    taken: Mapping[UUID, UUID]
    refused: Mapping[UUID, RefusedSeat]

    @property
    def all_taken(self) -> bool:
        return not self.refused


def hold_key(
    game_id: UUID, player_id: UUID, *, attempt: int, at: Instant, rescue: bool = False
) -> str:
    """The key a seat's hold is asked under: the game, the player, the attempt
    and the hour — a rescue's apart from the fill's (#545), since the two count
    their attempts on different streams and one game id carries both."""

    kind = "rescue" if rescue else "seat"
    return f"raketa-{kind}-{game_id}-{player_id}-{attempt}-{key_hour(at)}"


def _refusal_of(payment: Payment) -> FailureReason:
    return (
        FailureReason.AUTHENTICATION_REQUIRED
        if payment.status is PaymentStatus.AUTHENTICATION_REQUIRED
        else FailureReason.DECLINED
    )


@final
class ChargeTheSeats:
    def __init__(
        self,
        *,
        methods: PaymentMethodRepository,
        charges: SeatChargeRepository,
        sellers: Sellers,
        payers: Payers,
        provider: PaymentProvider,
        mail: MailQueue,
        app_link: str,
    ) -> None:
        self._methods = methods
        self._charges = charges
        self._sellers = sellers
        self._payers = payers
        self._provider = provider
        self._mail = mail
        self._app_link = app_link

    async def execute(
        self,
        game: GameToCharge,
        players: Sequence[UUID],
        *,
        attempt: int,
        at: Instant,
    ) -> SeatsCharged:
        invariant(len(set(players)) == len(players), f"a seat twice: {players}")
        seller = (await self._sellers.of([game.club_id])).get(game.club_id)
        invariant(
            seller is not None and seller.account_id is not None,
            f"a game filled at {game.club_id}, which takes no payments",
        )
        assert seller is not None and seller.account_id is not None
        confirmed = {
            charge.player_id: charge
            for charge in await self._charges.of_game(game.game_id)
            if charge.held_now
        }

        held: dict[UUID, Payment] = {}
        refused: dict[UUID, tuple[FailureReason, Payment | None]] = {}
        for player in players:
            if player in confirmed:
                continue
            outcome = await self._hold(
                game, player, seller=seller, attempt=attempt, at=at
            )
            if isinstance(outcome, Payment):
                held[player] = outcome
            else:
                refused[player] = outcome

        if not refused:
            return await self._take_every_seat(
                game, players, held=held, confirmed=confirmed, seller=seller, at=at
            )
        return await self._nobody_pays(
            game,
            held=held,
            confirmed=[confirmed[player] for player in players if player in confirmed],
            refused=refused,
            seller=seller,
            at=at,
        )

    async def _hold(
        self,
        game: GameToCharge,
        player: UUID,
        *,
        seller: Seller,
        attempt: int,
        at: Instant,
    ) -> Payment | tuple[FailureReason, Payment | None]:
        """One seat's hold, or why it could not be made."""

        assert seller.account_id is not None
        method = await self._methods.load(player)
        if method.method is None or method.customer_id is None:
            return FailureReason.NO_METHOD, None
        if method.terms_needed:
            # A brand the terms were not accepted for cannot be charged
            # off-session until its holder agrees again: the provider is not
            # asked (the mechanics §19).
            return FailureReason.TERMS_NEEDED, None
        key = hold_key(game.game_id, player, attempt=attempt, at=at, rescue=game.rescue)
        clone = await self._provider.clone_method(
            customer_id=method.customer_id,
            method_id=method.method.method_id,
            account_id=seller.account_id,
            idempotency_key=f"{key}-clone",
        )
        payment = await self._provider.authorise(
            account_id=seller.account_id,
            method_id=clone,
            amount_grosze=game.share_grosze,
            description=f"{game.sport.value.title()} · {seller.name}",
            metadata={"game_id": str(game.game_id), "player_id": str(player)},
            idempotency_key=key,
        )
        if payment.status is PaymentStatus.AUTHORISED:
            return payment
        return _refusal_of(payment), payment

    async def _take_every_seat(
        self,
        game: GameToCharge,
        players: Sequence[UUID],
        *,
        held: Mapping[UUID, Payment],
        confirmed: Mapping[UUID, SeatCharge],
        seller: Seller,
        at: Instant,
    ) -> SeatsCharged:
        taken: dict[UUID, UUID] = {}
        for player in players:
            charge = confirmed.get(player) or _a_hold(
                game, player, held[player], seller=seller, at=at
            )
            charge.take(booking_id=game.game_id, at=at)
            await self._charges.save(charge)
            taken[player] = charge.charge_id
        payers = await self._payers.of(players)
        for player in players:
            payer = payers.get(player)
            if payer is None:
                continue
            await self._mail.enqueue(
                game_booked_email(
                    to=payer.email,
                    name=payer.name,
                    club=seller.name,
                    court=game.court_name,
                    sport=game.sport,
                    starts_at=game.starts_at,
                    paid_grosze=game.share_grosze,
                    free_to_leave_until=game.free_to_leave_until,
                    fee_estimate_grosze=estimated_card_fee(game.share_grosze),
                    app_link=self._app_link,
                    booked_on_a_payment=game.booked_on_a_payment
                    and player != game.filled_by,
                ),
                at=at,
            )
        return SeatsCharged(taken=taken, refused={})

    async def _nobody_pays(
        self,
        game: GameToCharge,
        *,
        held: Mapping[UUID, Payment],
        confirmed: Sequence[SeatCharge],
        refused: Mapping[UUID, tuple[FailureReason, Payment | None]],
        seller: Seller,
        at: Instant,
    ) -> SeatsCharged:
        assert seller.account_id is not None
        made = [
            _a_hold(game, player, payment, seller=seller, at=at)
            for player, payment in held.items()
        ]
        if game.pay_by is None:
            for charge in [*made, *confirmed]:
                charge.release(at=at)
                await self._charges.save(charge)
        else:
            # Time to pay: every hold waits on its card for the payment in
            # time, and the game books on them (Q109).
            for charge in made:
                await self._charges.save(charge)
        seats: dict[UUID, RefusedSeat] = {}
        for player, (reason, answer) in refused.items():
            charge = SeatCharge.refused(
                charge_id=new_uuid(),
                player_id=player,
                game_id=game.game_id,
                club_id=game.club_id,
                account_id=seller.account_id,
                amount_grosze=game.share_grosze,
                sport=game.sport,
                starts_at=game.starts_at,
                reason=reason,
                payment=answer,
                at=at,
            )
            await self._charges.save(charge)
            seats[player] = RefusedSeat(charge_id=charge.charge_id, reason=reason)
        if game.pay_by is None and not game.rescue:
            # No time is left to pay — the book-by had come at the club's yes:
            # the game is called off, and told so; there is nothing to confirm.
            return SeatsCharged(taken={}, refused=seats)
        payers = await self._payers.of(list(refused))
        for player, seat in seats.items():
            payer = payers.get(player)
            if payer is None:
                continue
            await self._mail.enqueue(
                confirm_payment_email(
                    to=payer.email,
                    club=seller.name,
                    sport=game.sport,
                    starts_at=game.starts_at,
                    amount_grosze=game.share_grosze,
                    reason=seat.reason,
                    app_link=self._app_link,
                    rescue=game.rescue,
                    pay_by=game.paying_until.get(player, game.pay_by),
                ),
                at=at,
            )
        return SeatsCharged(taken={}, refused=seats)


def _a_hold(
    game: GameToCharge, player: UUID, payment: Payment, *, seller: Seller, at: Instant
) -> SeatCharge:
    """A hold the provider just made, as the charge it is born."""

    assert seller.account_id is not None
    return SeatCharge.held(
        charge_id=new_uuid(),
        player_id=player,
        game_id=game.game_id,
        club_id=game.club_id,
        account_id=seller.account_id,
        payment=payment,
        sport=game.sport,
        starts_at=game.starts_at,
        at=at,
    )


@final
class ReleaseCharges:
    """Let go of every charge on a game that it will not be paid with — a
    refused payment the seat was taken from, or a hold confirmed for a game
    that filled without it or never filled. **No commit.**"""

    def __init__(self, *, charges: SeatChargeRepository) -> None:
        self._charges = charges

    async def execute(
        self,
        game_id: UUID,
        *,
        keeping: Collection[UUID],
        of_player: UUID | None = None,
        at: Instant,
    ) -> int:
        """Release every undecided charge on ``game_id`` that is not one of
        ``keeping`` — only ``of_player``'s, when one is named. Answers how many
        were released."""

        released = 0
        for charge in await self._charges.of_game(game_id):
            if charge.charge_id in keeping:
                continue
            if of_player is not None and charge.player_id != of_player:
                continue
            if charge.release(at=at):
                await self._charges.save(charge)
                released += 1
        return released


@final
class PaymentToConfirmOn:
    """This player's refused payment for this game still waiting for them —
    what a rescue's second *I'm in* is told to confirm rather than asking the
    bank the same question again (#545)."""

    def __init__(self, *, charges: SeatChargeRepository) -> None:
        self._charges = charges

    async def execute(self, game_id: UUID, *, player_id: UUID) -> UUID | None:
        for charge in reversed(await self._charges.of_game(game_id)):
            if charge.player_id == player_id and charge.awaits_its_player:
                return charge.charge_id
        return None


@final
@dataclass(frozen=True, slots=True)
class ConfirmedCharge:
    """A refused charge its player confirmed: held now, for this game."""

    charge_id: UUID
    game_id: UUID


@final
class ConfirmSeatCharge:
    """*I confirmed my payment in the app.* **Asked of the provider, never
    taken on the phone's word**: the payment is read as it stands, and only a
    payment it holds is recorded as confirmed. No commit — the yes it stands for
    is the caller's, in the same transaction."""

    def __init__(
        self, *, charges: SeatChargeRepository, provider: PaymentProvider
    ) -> None:
        self._charges = charges
        self._provider = provider

    async def execute(
        self, charge_id: UUID, *, player_id: UUID, at: Instant
    ) -> ConfirmedCharge:
        charge = await self._charges.load(charge_id)
        if charge is None or charge.player_id != player_id:
            raise SeatChargeNotFound()
        if charge.status is SeatChargeStatus.AUTHORISED:
            # Confirmed already — by an earlier request, or by the provider's
            # notice that arrived first.
            return ConfirmedCharge(charge_id=charge_id, game_id=charge.game_id)
        if charge.status is not SeatChargeStatus.FAILED or charge.payment_id is None:
            raise PaymentNotConfirmed(
                status=charge.status.value
                if charge.status is not SeatChargeStatus.FAILED
                else "NOTHING_TO_CONFIRM"
            )
        payment = await self._provider.read_payment(
            account_id=charge.account_id, payment_id=charge.payment_id
        )
        if payment.status is not PaymentStatus.AUTHORISED:
            raise PaymentNotConfirmed(status=payment.status.value)
        charge.confirm(at=at, last_moment=payment.last_moment)
        await self._charges.save(charge)
        return ConfirmedCharge(charge_id=charge_id, game_id=charge.game_id)


@final
@dataclass(frozen=True, slots=True)
class ChargeToConfirm:
    """What the phone needs to confirm a refused payment on the club's
    account: the payment's secret and the seller's account, asked of the
    provider now and never recorded."""

    client_secret: str
    account_id: str
    publishable_key: str


@final
@dataclass(frozen=True, slots=True)
class SeatChargeReading:
    charge: SeatCharge
    club_name: str | None
    #: Present exactly while the payment waits for its player.
    to_confirm: ChargeToConfirm | None


@final
class ReadSeatCharge:
    """One of the reader's own charges — and, while its payment waits for them,
    what the phone confirms it with."""

    def __init__(
        self,
        *,
        charges: SeatChargeRepository,
        sellers: Sellers,
        provider: PaymentProvider,
    ) -> None:
        self._charges = charges
        self._sellers = sellers
        self._provider = provider

    async def execute(self, charge_id: UUID, *, player_id: UUID) -> SeatChargeReading:
        charge = await self._charges.load(charge_id)
        if charge is None or charge.player_id != player_id:
            raise SeatChargeNotFound()
        seller = (await self._sellers.of([charge.club_id])).get(charge.club_id)
        to_confirm = None
        if charge.awaits_its_player:
            assert charge.payment_id is not None
            payment = await self._provider.read_payment(
                account_id=charge.account_id, payment_id=charge.payment_id
            )
            if payment.client_secret is not None:
                to_confirm = ChargeToConfirm(
                    client_secret=payment.client_secret,
                    account_id=charge.account_id,
                    publishable_key=self._provider.publishable_key(),
                )
        return SeatChargeReading(
            charge=charge,
            club_name=None if seller is None else seller.name,
            to_confirm=to_confirm,
        )


class ReceiptKind(StrEnum):
    """Which way the money went."""

    #: A share paid.
    CHARGE = "CHARGE"
    #: A share given back (#544).
    REFUND = "REFUND"


@final
@dataclass(frozen=True, slots=True)
class Receipt:
    """Money that moved for the player: to whom, for which game, how much,
    which way, when."""

    charge: SeatCharge
    club_name: str | None
    kind: ReceiptKind = ReceiptKind.CHARGE

    @property
    def amount_grosze(self) -> int:
        """What was paid, or what came back — always positive."""

        if self.kind is ReceiptKind.REFUND:
            assert self.charge.refund_given is not None
            return self.charge.refund_given.amount_grosze
        return self.charge.amount_grosze

    @property
    def card_fee_grosze(self) -> int | None:
        """The card fee kept back from a refund; ``None`` on a charge."""

        if self.kind is ReceiptKind.REFUND:
            assert self.charge.refund_given is not None
            return self.charge.refund_given.fee_withheld_grosze
        return None

    @property
    def at(self) -> Instant:
        """When the money moved: taken, or given back — the act that decided
        the refund, a leaving or a call-off, rather than the provider's answer
        moments later."""

        if self.kind is ReceiptKind.REFUND:
            assert self.charge.refund_decided_at is not None
            return self.charge.refund_decided_at
        return self.charge.taken_at or self.charge.opened_at


@final
class ReadReceipts:
    """You › Payments' *RECEIPTS*: every share the reader paid and every share
    given back (#544), **the club named as the seller**, the latest first. A
    hold let go is not a receipt — nobody paid it — and a refund is one once the
    provider has given it, with the card fee it kept."""

    def __init__(self, *, charges: SeatChargeRepository, sellers: Sellers) -> None:
        self._charges = charges
        self._sellers = sellers

    async def execute(self, player_id: UUID) -> tuple[Receipt, ...]:
        paid = [
            charge
            for charge in await self._charges.paid_by(player_id)
            if charge.status in PAID
        ]
        sellers = await self._sellers.of({charge.club_id for charge in paid})
        receipts: list[Receipt] = []
        for charge in paid:
            club_name = (
                sellers[charge.club_id].name if charge.club_id in sellers else None
            )
            receipts.append(Receipt(charge=charge, club_name=club_name))
            if charge.refund_given is not None:
                receipts.append(
                    Receipt(
                        charge=charge, club_name=club_name, kind=ReceiptKind.REFUND
                    )
                )
        # Latest first; a refund given at the moment of its charge after it.
        return tuple(
            sorted(
                receipts,
                key=lambda receipt: (receipt.at, receipt.kind is ReceiptKind.REFUND),
                reverse=True,
            )
        )
