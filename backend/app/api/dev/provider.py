"""The payment provider's controls: a card steered, a payment the bank
confirms, a refund delivered, a notice replayed (``docs/adr/0194`` §2, §3;
#591).

**The provider is the process's in-process fake** (``FakePayments``) — the one
every request and the outbox move money through on a laptop — and these routes
steer it, the way Stripe's test cards and dashboard steer the real one. Any
other provider is refused ``provider_not_the_fake``: there is nothing here to
steer Stripe with, and a console that tried would be moving real money.

**Four controls, each the provider's half of something the app does**:

- **A saved card set to succeed, decline or ask for the bank's check** — the
  saved card the player's payments are cloned from, so the next fill's hold
  answers as that card would — **and of a kind and a network** (ADR-0190's
  2026-10-10 amendment): a personal EU, business, UK or non-European card, whose
  fee is kept when the share is taken, on Visa or Mastercard, whose hold lasts
  4 days 18 hours or 7 days. Only the fake's record of the card moves — the
  player's own method still says the brand they saved. Only a seed account's
  card (``not_a_seed_account``), and only one that is saved (``no_saved_card``).
- **The bank confirms a payment that waited for its player.** A phone confirms
  a refused payment with the provider itself; a laptop's phone has no provider
  to confirm with (its key is the fake's), so its *Confirm* would find the
  payment still waiting. This is the bank saying yes on the phone — the check
  passed, or another card typed — after which the phone's own *Confirm* is the
  yes again, as it is anywhere.
- **A refund delivered.** A refund is decided in the act and made from the
  outbox; with **refunds waiting** the fake gives none until told, so the
  tester can see one decided and not yet given. *Deliver* lets one through and
  runs the outbox's own step for that charge at once (``SettleSeatCharges``).
  **A waiting refund holds back its whole delivery**, as a provider that is
  down does: the decision's email went in the act, but the player's in-app
  notice and the receipt's *refund* row arrive with the money, and the
  server's log records each retry. The switch is the process's, so every
  refund waits — on a laptop, every account is the seed's.
- **A notice replayed.** The fake records the notice Stripe would have sent
  for every move of a payment; a delivery hands each, in the order given — the
  same one twice, or newest first — to ``ReceivePaymentNotice``, the webhook's
  own handling, past nothing but the signature check (ADR-0194 §3).

**Only a seed account's money moves**: a card, a payment the bank confirms, a
refund delivered and a notice replayed are each refused ``not_a_seed_account``
when the share is anybody else's.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from collections.abc import Collection, Mapping
from datetime import datetime
from typing import Annotated, Any, Final
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import DbSession, UnitOfWorkDep, UserRepositoryDep
from app.api.dev.accounts import refuse_unless_a_seed_account
from app.api.dev.board import (
    CARD_BEHAVIOURS,
    CardNetwork,
    CardOutcome,
    PersonRef,
    network_of,
    outcome_of,
    steerable,
)
from app.api.dev.dependencies import PlayerNamesDep, SettleSeatChargesDep
from app.core.exception_handlers import ErrorResponse
from app.kernel import invariant
from app.modules.payments.domain.entered_cards import A_CARD, CardKind
from app.modules.payments.domain.errors import SeatChargeNotFound
from app.modules.payments.domain.payment_method import SavedMethod
from app.modules.payments.domain.ports import (
    PaymentMethodRepository,
    SeatChargeRepository,
)
from app.modules.payments.domain.provider import AWAITING_THE_PLAYER, PaymentStatus
from app.modules.payments.domain.seat_charge import SeatCharge
from app.modules.payments.infrastructure.fake_payments import FakePayments
from app.modules.payments.infrastructure.payment_models import PaymentNoticeORM
from app.modules.payments.presentation.dependencies import (
    PaymentMethodRepositoryDep,
    PaymentProviderDep,
    ReceivePaymentNoticeDep,
    SeatChargeRepositoryDep,
)
from app.modules.users.domain.ports import UserRepository
from app.shared.domain.errors import ConflictError, NotFoundError

router = APIRouter(prefix="/payments", tags=["dev"])

#: How many notices one delivery may hand over — a game's are a handful.
MAX_DELIVERIES: Final = 50


# --------------------------------------------------------------------------- #
# Refusals
# --------------------------------------------------------------------------- #


class ProviderNotTheFake(ConflictError):
    code = "provider_not_the_fake"

    def __init__(self) -> None:
        super().__init__(
            "This process moves money through a real provider, not the "
            "in-process fake: the console has nothing to steer it with."
        )


class NoSavedCard(ConflictError):
    code = "no_saved_card"

    def __init__(self) -> None:
        super().__init__("This player has no card saved for the provider to steer.")


class PaymentNotWaitingForItsPlayer(ConflictError):
    code = "payment_not_waiting_for_its_player"

    def __init__(self) -> None:
        super().__init__(
            "This payment is not waiting for its player: only a share refused "
            "at the fill or a rescue, whose bank wants the player, can be "
            "confirmed at the bank."
        )


class NoRefundDecided(ConflictError):
    code = "no_refund_decided"

    def __init__(self) -> None:
        super().__init__(
            "Nothing was decided to be given back on this share: a refund is "
            "decided by a leaving, a call-off or a cancel, and only then made."
        )


class NoticeNotFound(NotFoundError):
    code = "notice_not_found"

    def __init__(self, unknown: Collection[str]) -> None:
        super().__init__(
            "The provider never sent these notices; nothing was delivered.",
            details={"notice_ids": sorted(unknown)},
        )


# --------------------------------------------------------------------------- #
# The fake, as a request dependency
# --------------------------------------------------------------------------- #


def the_fake(provider: PaymentProviderDep) -> FakePayments:
    """The process's fake provider, or ``provider_not_the_fake``."""

    fake = steerable(provider)
    if fake is None:
        raise ProviderNotTheFake()
    return fake


TheFakeDep = Annotated[FakePayments, Depends(the_fake)]


# --------------------------------------------------------------------------- #
# The wire
# --------------------------------------------------------------------------- #


class SteerCardRequest(BaseModel):
    outcome: CardOutcome | None = Field(
        default=None,
        description="What the next payment does; left as it is if omitted.",
    )
    kind: CardKind | None = Field(
        default=None,
        description=(
            "Which kind of card it is — the fee kept when a share is taken; "
            "left as it is if omitted."
        ),
    )
    network: CardNetwork | None = Field(
        default=None,
        description=(
            "Which network holds a share on it — how long a hold lasts; left "
            "as it is if omitted."
        ),
    )


class SteeredCardResponse(BaseModel):
    player_id: UUID
    brand: str
    last_four: str
    outcome: CardOutcome
    kind: CardKind
    network: CardNetwork
    says: str = Field(description="What happened, for the tester.")


class BankConfirmedResponse(BaseModel):
    charge_id: UUID
    says: str = Field(description="What happened, for the tester.")


class RefundsRequest(BaseModel):
    wait: bool = Field(
        description=(
            "`true` — every refund asked of the provider waits until it is "
            "delivered here; the outbox asks again meanwhile, as of a provider "
            "that is down. `false` — refunds are given when asked, as at "
            "Stripe; any still waiting go on the outbox's next try."
        )
    )


class RefundsResponse(BaseModel):
    wait: bool
    says: str = Field(description="What happened, for the tester.")


class RefundDeliveredResponse(BaseModel):
    charge_id: UUID
    #: ``None`` while a refund less the fee waits for a fee not yet known.
    given_back_grosze: int | None
    fee_withheld_grosze: int | None
    given_at: datetime | None
    says: str = Field(description="What happened, for the tester.")


class NoticeRow(BaseModel):
    notice_id: str
    kind: str = Field(description="As Stripe names it, `payment_intent.*`.")
    status: PaymentStatus = Field(
        description=(
            "Where the move left the payment. The notice carries none of it: "
            "it is read as a prompt, and the payment as it stands now."
        )
    )
    payment_id: str
    charge_id: UUID
    player: PersonRef
    read: bool = Field(
        description="Raketa has read it — delivering it again is a no-op."
    )


class NoticesResponse(BaseModel):
    notices: list[NoticeRow] = Field(
        description="Every notice about the game's payments, in the order sent."
    )


class DeliveryRequest(BaseModel):
    notice_ids: list[str] = Field(
        min_length=1,
        max_length=MAX_DELIVERIES,
        description=(
            "Delivered one after another, in this order — the same one twice is "
            "a replay, newest first is out of order."
        ),
    )


class Delivery(BaseModel):
    notice_id: str
    kind: str
    read: bool = Field(
        description="`true` — read and acted on; `false` — read before, nothing done."
    )


class DeliveryResponse(BaseModel):
    deliveries: list[Delivery]
    says: str = Field(description="What happened, for the tester.")


_REFUSED: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": (
            "`not_a_seed_account` — the player whose money it is is not an "
            "account the seed created."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "`seat_charge_not_found`, or `notice_not_found`.",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "`provider_not_the_fake` — nothing to steer. Otherwise the "
            "control's own refusal, and why."
        ),
    },
}


# --------------------------------------------------------------------------- #
# A card steered
# --------------------------------------------------------------------------- #


@router.put(
    "/cards/{player_id}",
    response_model=SteeredCardResponse,
    responses=_REFUSED,
    summary="Set a player's saved card: what it does, its kind and its network",
    description=(
        "What the next payment cloned from this player's saved card does — the "
        "next fill's hold, a rescue's, a holding's — which kind of card "
        "it is, so the fee kept when its share is taken, and which network "
        "holds it, so how long a hold lasts. Each field omitted is left as it is."
    ),
)
async def steer_a_card(
    player_id: UUID,
    payload: SteerCardRequest,
    fake: TheFakeDep,
    users: UserRepositoryDep,
    methods: PaymentMethodRepositoryDep,
) -> SteeredCardResponse:
    await refuse_unless_a_seed_account(users, player_id)
    saved = await steer(fake, methods, player_id, payload.outcome)
    fake.card_is(
        saved.method_id,
        kind=payload.kind,
        network=None if payload.network is None else payload.network.value,
    )
    outcome = outcome_of(fake.card_behaviour_of(saved.method_id))
    kind = fake.card_kind_of(saved.method_id)
    network = network_of(fake.card_network_of(saved.method_id))
    return SteeredCardResponse(
        player_id=player_id,
        brand=saved.brand,
        last_four=saved.last_four,
        outcome=outcome,
        kind=kind,
        network=network,
        says=(
            f"Their {saved.brand} •••• {saved.last_four} {_SAYS[outcome]}, "
            f"{_KINDS[kind]}, {_NETWORKS[network]}, from the next payment on."
        ),
    )


async def steer(
    fake: FakePayments,
    methods: PaymentMethodRepository,
    player_id: UUID,
    outcome: CardOutcome | None,
) -> SavedMethod:
    """Set what the player's saved card does with its next payment — or
    ``no_saved_card``; ``None`` leaves it as it is. The card it is, as the
    player's stream has it."""

    saved = (await methods.load(player_id)).method
    if saved is None:
        raise NoSavedCard()
    if outcome is not None:
        fake.card_behaves(saved.method_id, CARD_BEHAVIOURS[outcome])
    return saved


_SAYS: Mapping[CardOutcome, str] = {
    CardOutcome.SUCCEEDS: "pays",
    CardOutcome.DECLINES: "is declined",
    CardOutcome.ASKS_FOR_VERIFICATION: "asks for the bank's check",
}

_KINDS: Mapping[CardKind, str] = {
    CardKind.PERSONAL_EU: "as a personal EU card (1,5 % + 1 zł kept when taken)",
    CardKind.BUSINESS: "as a business card (1,9 % + 1 zł kept when taken)",
    CardKind.UK: "as a UK card (2,5 % + 1 zł kept when taken)",
    CardKind.OUTSIDE_EUROPE: (
        "as a card from outside Europe (3,25 % + 1 zł kept when taken)"
    ),
}

_NETWORKS: Mapping[CardNetwork, str] = {
    CardNetwork.VISA: "held on Visa (a hold lasts 4 days 18 hours)",
    CardNetwork.MASTERCARD: "held on Mastercard (a hold lasts 7 days)",
}


# --------------------------------------------------------------------------- #
# The bank confirms
# --------------------------------------------------------------------------- #


async def _seed_charge(
    charges: SeatChargeRepository, users: UserRepository, charge_id: UUID
) -> SeatCharge:
    """The charge, once it is a seed account's — the console moves nobody
    else's money."""

    charge = await charges.load(charge_id)
    if charge is None:
        raise SeatChargeNotFound()
    await refuse_unless_a_seed_account(users, charge.player_id)
    return charge


@router.post(
    "/charges/{charge_id}/bank-confirms",
    response_model=BankConfirmedResponse,
    responses=_REFUSED,
    summary="The bank confirms a payment that waited for its player",
    description=(
        "What the phone's confirmation does with the bank, which a laptop's "
        "phone cannot reach: the check passed — or, for a declined payment, "
        "another card typed and its bank agreeing. The provider holds the "
        "payment now; the player's own *Confirm* is then the yes again."
    ),
)
async def the_bank_confirms(
    charge_id: UUID,
    fake: TheFakeDep,
    charges: SeatChargeRepositoryDep,
    users: UserRepositoryDep,
) -> BankConfirmedResponse:
    charge = await _seed_charge(charges, users, charge_id)
    if not charge.awaits_its_player or charge.payment_id is None:
        raise PaymentNotWaitingForItsPlayer()
    payment = await fake.read_payment(
        account_id=charge.account_id, payment_id=charge.payment_id
    )
    if payment.status not in AWAITING_THE_PLAYER:
        raise PaymentNotWaitingForItsPlayer()
    declined = payment.status is PaymentStatus.DECLINED
    fake.phone_confirms_payment(
        charge.payment_id, with_card=A_CARD if declined else None
    )
    return BankConfirmedResponse(
        charge_id=charge_id,
        says=(
            (
                "Another card was typed and its bank agreed"
                if declined
                else "The bank's check passed"
            )
            + ": the provider holds the payment. Confirm it on the phone."
        ),
    )


# --------------------------------------------------------------------------- #
# Refunds
# --------------------------------------------------------------------------- #


@router.put(
    "/refunds",
    response_model=RefundsResponse,
    responses=_REFUSED,
    summary="Make refunds wait, or give them when asked",
)
async def refunds_wait(payload: RefundsRequest, fake: TheFakeDep) -> RefundsResponse:
    fake.refunds_wait = payload.wait
    return RefundsResponse(
        wait=fake.refunds_wait,
        says=(
            "Refunds wait until you deliver each one. Meanwhile the outbox asks "
            "again every second, and the server's log says it could not."
            if payload.wait
            else "Refunds are given when asked; any waiting go on the next try."
        ),
    )


@router.post(
    "/charges/{charge_id}/refund",
    response_model=RefundDeliveredResponse,
    responses=_REFUSED,
    summary="Deliver a share's refund now",
    description=(
        "The refund decided on this share, given by the provider and recorded "
        "now — the outbox's own step for the charge, run at once. A refund "
        "given already is answered as it was."
    ),
)
async def deliver_a_refund(
    charge_id: UUID,
    fake: TheFakeDep,
    charges: SeatChargeRepositoryDep,
    users: UserRepositoryDep,
    settle: SettleSeatChargesDep,
    uow: UnitOfWorkDep,
) -> RefundDeliveredResponse:
    charge = await _seed_charge(charges, users, charge_id)
    if charge.refund_withholds_fee is None:
        raise NoRefundDecided()
    given_already = charge.refund_given is not None
    if not given_already:
        fake.gives_refund(invariant(charge.payment_id, f"{charge_id} paid, no payment"))
        await settle.settle(charge_id)
        # The press is the outbox's delivery of this charge, and a delivery
        # commits what its step recorded — ``settle`` itself never does.
        await uow.commit()
        charge = await _seed_charge(charges, users, charge_id)
    given = charge.refund_given
    back = charge.given_back_grosze
    return RefundDeliveredResponse(
        charge_id=charge_id,
        given_back_grosze=back,
        fee_withheld_grosze=None if given is None else given.fee_withheld_grosze,
        given_at=None if given is None else given.at,
        says=(
            "Given already."
            if given_already
            # Settled just now, so what came back is the provider's answer.
            else f"Given back: {invariant(back, 'a refund given') / 100:.2f} zł."
        ),
    )


# --------------------------------------------------------------------------- #
# Notices
# --------------------------------------------------------------------------- #


async def _read_already(db: AsyncSession, notice_ids: Collection[str]) -> set[str]:
    """Which of these notices Raketa has read — the inbox's own rows."""

    if not notice_ids:
        return set()
    rows = await db.execute(
        select(PaymentNoticeORM.notice_id).where(
            PaymentNoticeORM.notice_id.in_(notice_ids)
        )
    )
    return set(rows.scalars())


@router.get(
    "/notices",
    response_model=NoticesResponse,
    responses=_REFUSED,
    summary="The notices the provider sent about a game's payments",
)
async def notices(
    game_id: UUID,
    db: DbSession,
    fake: TheFakeDep,
    charges: SeatChargeRepositoryDep,
    names: PlayerNamesDep,
) -> NoticesResponse:
    by_payment = {
        charge.payment_id: charge
        for charge in await charges.of_game(game_id)
        if charge.payment_id is not None
    }
    sent = [one for one in fake.notices if one.notice.payment_id in by_payment]
    read = await _read_already(db, [one.notice.notice_id for one in sent])
    named = await names.names_of({charge.player_id for charge in by_payment.values()})
    rows = []
    for one in sent:
        charge = by_payment[one.notice.payment_id]
        rows.append(
            NoticeRow(
                notice_id=one.notice.notice_id,
                kind=one.kind,
                status=one.status,
                payment_id=one.notice.payment_id,
                charge_id=charge.charge_id,
                player=PersonRef(
                    player_id=charge.player_id, nickname=named.get(charge.player_id)
                ),
                read=one.notice.notice_id in read,
            )
        )
    return NoticesResponse(notices=rows)


@router.post(
    "/notices/delivery",
    response_model=DeliveryResponse,
    responses=_REFUSED,
    summary="Deliver notices the provider sent — twice, or out of order",
    description=(
        "Each notice, in the order given, to the webhook's own handling: read "
        "once, and what it names read from the provider as it stands. An id "
        "the provider never sent refuses the whole delivery before any is read."
    ),
)
async def deliver_notices(
    payload: DeliveryRequest,
    fake: TheFakeDep,
    receive: ReceivePaymentNoticeDep,
    charges: SeatChargeRepositoryDep,
    users: UserRepositoryDep,
) -> DeliveryResponse:
    sent = {one.notice.notice_id: one for one in fake.notices}
    unknown = {notice_id for notice_id in payload.notice_ids if notice_id not in sent}
    if unknown:
        raise NoticeNotFound(unknown)
    for payment_id in {
        sent[notice_id].notice.payment_id for notice_id in payload.notice_ids
    }:
        charge = await charges.by_payment(payment_id)
        if charge is not None:
            await refuse_unless_a_seed_account(users, charge.player_id)
    deliveries = []
    for notice_id in payload.notice_ids:
        one = sent[notice_id]
        deliveries.append(
            Delivery(
                notice_id=notice_id,
                kind=one.kind,
                read=await receive.execute(one.notice),
            )
        )
    acted = sum(1 for delivery in deliveries if delivery.read)
    return DeliveryResponse(
        deliveries=deliveries,
        says=(
            f"{len(deliveries)} delivered: {acted} read, "
            f"{len(deliveries) - acted} read before and acknowledged."
        ),
    )
