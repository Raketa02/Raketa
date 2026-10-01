"""Request-scoped declarations for the Payments context.

When each port is built and how long it lives; **what** is built is the
composition root's (``app/bootstrap/composition.py``). The provider is the
process's — one fake on a laptop, one Stripe client deployed — and every test
replaces it with its own fake (``tests/conftest.py``).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    SettingsDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_connected_account_notices,
    build_connected_accounts,
    build_notice_inbox,
    build_onboarding_pages,
    build_payments_accounts,
    build_payment_commitments,
    build_payment_method_repository,
    build_payment_notices,
    build_payment_provider,
    build_read_receipts,
    build_read_seat_charge,
    build_seat_charge_repository,
)
from app.modules.clubs.application.payments_account import ConnectPayments
from app.modules.clubs.presentation.dependencies import (
    ClubCourtsRepositoryDep,
    ClubRepositoryDep,
)
from app.modules.payments.application.method import (
    ReadPaymentMethod,
    RemovePaymentMethod,
)
from app.modules.payments.application.notices import ReceivePaymentNotice
from app.modules.payments.application.seat_charges import (
    ReadReceipts,
    ReadSeatCharge,
)
from app.modules.payments.application.setup import (
    AcceptPaymentTerms,
    ConfirmPaymentSetup,
    StartPaymentSetup,
)
from app.modules.payments.domain.notices import PaymentNotices
from app.modules.payments.domain.ports import (
    ConnectedAccounts,
    NoticeInbox,
    PaymentCommitments,
    PaymentMethodRepository,
    SeatChargeRepository,
)
from app.modules.payments.domain.provider import PaymentProvider


def get_payment_provider(settings: SettingsDep) -> PaymentProvider:
    return build_payment_provider(settings)


PaymentProviderDep = Annotated[PaymentProvider, Depends(get_payment_provider)]


def get_payment_notices(settings: SettingsDep) -> PaymentNotices:
    return build_payment_notices(settings)


PaymentNoticesDep = Annotated[PaymentNotices, Depends(get_payment_notices)]


def get_connected_account_notices(settings: SettingsDep) -> PaymentNotices:
    return build_connected_account_notices(settings)


ConnectedAccountNoticesDep = Annotated[
    PaymentNotices, Depends(get_connected_account_notices)
]


def get_payment_method_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> PaymentMethodRepository:
    return build_payment_method_repository(db, event_store=event_store, events=events)


PaymentMethodRepositoryDep = Annotated[
    PaymentMethodRepository, Depends(get_payment_method_repository)
]


def get_payment_commitments(db: DbSession) -> PaymentCommitments:
    return build_payment_commitments(db)


PaymentCommitmentsDep = Annotated[PaymentCommitments, Depends(get_payment_commitments)]


def get_notice_inbox(db: DbSession) -> NoticeInbox:
    return build_notice_inbox(db)


NoticeInboxDep = Annotated[NoticeInbox, Depends(get_notice_inbox)]


def get_start_payment_setup(
    methods: PaymentMethodRepositoryDep,
    provider: PaymentProviderDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> StartPaymentSetup:
    return StartPaymentSetup(methods=methods, provider=provider, uow=uow, clock=clock)


StartPaymentSetupDep = Annotated[StartPaymentSetup, Depends(get_start_payment_setup)]


def get_accept_payment_terms(
    methods: PaymentMethodRepositoryDep,
    provider: PaymentProviderDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> AcceptPaymentTerms:
    return AcceptPaymentTerms(methods=methods, provider=provider, uow=uow, clock=clock)


AcceptPaymentTermsDep = Annotated[AcceptPaymentTerms, Depends(get_accept_payment_terms)]


def get_confirm_payment_setup(
    methods: PaymentMethodRepositoryDep,
    provider: PaymentProviderDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ConfirmPaymentSetup:
    return ConfirmPaymentSetup(methods=methods, provider=provider, uow=uow, clock=clock)


ConfirmPaymentSetupDep = Annotated[
    ConfirmPaymentSetup, Depends(get_confirm_payment_setup)
]


def get_read_payment_method(methods: PaymentMethodRepositoryDep) -> ReadPaymentMethod:
    return ReadPaymentMethod(methods=methods)


ReadPaymentMethodDep = Annotated[ReadPaymentMethod, Depends(get_read_payment_method)]


def get_remove_payment_method(
    methods: PaymentMethodRepositoryDep,
    commitments: PaymentCommitmentsDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> RemovePaymentMethod:
    return RemovePaymentMethod(
        methods=methods, commitments=commitments, uow=uow, clock=clock
    )


RemovePaymentMethodDep = Annotated[
    RemovePaymentMethod, Depends(get_remove_payment_method)
]


def get_connected_accounts(
    db: DbSession,
    provider: PaymentProviderDep,
    settings: SettingsDep,
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
    clock: ClockDep,
) -> ConnectedAccounts:
    return build_connected_accounts(
        db,
        provider=provider,
        settings=settings,
        event_store=event_store,
        events=events,
        clock=clock,
    )


ConnectedAccountsDep = Annotated[ConnectedAccounts, Depends(get_connected_accounts)]


def get_seat_charge_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> SeatChargeRepository:
    return build_seat_charge_repository(db, event_store=event_store, events=events)


SeatChargeRepositoryDep = Annotated[
    SeatChargeRepository, Depends(get_seat_charge_repository)
]


def get_receive_payment_notice(
    inbox: NoticeInboxDep,
    methods: PaymentMethodRepositoryDep,
    accounts: ConnectedAccountsDep,
    charges: SeatChargeRepositoryDep,
    provider: PaymentProviderDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ReceivePaymentNotice:
    return ReceivePaymentNotice(
        inbox=inbox,
        methods=methods,
        accounts=accounts,
        charges=charges,
        provider=provider,
        uow=uow,
        clock=clock,
    )


ReceivePaymentNoticeDep = Annotated[
    ReceivePaymentNotice, Depends(get_receive_payment_notice)
]


# --- A club's payments account, on the club surface (#537) -----------------


def get_connect_payments(
    clubs: ClubRepositoryDep,
    courts: ClubCourtsRepositoryDep,
    provider: PaymentProviderDep,
    settings: SettingsDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ConnectPayments:
    return ConnectPayments(
        clubs=clubs,
        courts=courts,
        payments_accounts=build_payments_accounts(provider),
        pages=build_onboarding_pages(settings),
        uow=uow,
        clock=clock,
    )


ConnectPaymentsDep = Annotated[ConnectPayments, Depends(get_connect_payments)]


# --- A player's seat charges and receipts (#541) -----------------------------


def get_read_seat_charge(
    db: DbSession, provider: PaymentProviderDep
) -> ReadSeatCharge:
    return build_read_seat_charge(db, provider=provider)


ReadSeatChargeDep = Annotated[ReadSeatCharge, Depends(get_read_seat_charge)]


def get_read_receipts(db: DbSession) -> ReadReceipts:
    return build_read_receipts(db)


ReadReceiptsDep = Annotated[ReadReceipts, Depends(get_read_receipts)]
