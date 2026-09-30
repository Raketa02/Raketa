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
    build_notice_inbox,
    build_payment_commitments,
    build_payment_method_repository,
    build_payment_notices,
    build_payment_provider,
)
from app.modules.payments.application.method import (
    ReadPaymentMethod,
    RemovePaymentMethod,
)
from app.modules.payments.application.notices import ReceivePaymentNotice
from app.modules.payments.application.setup import (
    AcceptPaymentTerms,
    ConfirmPaymentSetup,
    StartPaymentSetup,
)
from app.modules.payments.domain.notices import PaymentNotices
from app.modules.payments.domain.ports import (
    NoticeInbox,
    PaymentCommitments,
    PaymentMethodRepository,
)
from app.modules.payments.domain.provider import PaymentProvider


def get_payment_provider(settings: SettingsDep) -> PaymentProvider:
    return build_payment_provider(settings)


PaymentProviderDep = Annotated[PaymentProvider, Depends(get_payment_provider)]


def get_payment_notices(settings: SettingsDep) -> PaymentNotices:
    return build_payment_notices(settings)


PaymentNoticesDep = Annotated[PaymentNotices, Depends(get_payment_notices)]


def get_payment_method_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> PaymentMethodRepository:
    return build_payment_method_repository(db, event_store=event_store, events=events)


PaymentMethodRepositoryDep = Annotated[
    PaymentMethodRepository, Depends(get_payment_method_repository)
]


def get_payment_commitments() -> PaymentCommitments:
    return build_payment_commitments()


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


def get_receive_payment_notice(
    inbox: NoticeInboxDep,
    methods: PaymentMethodRepositoryDep,
    provider: PaymentProviderDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ReceivePaymentNotice:
    return ReceivePaymentNotice(
        inbox=inbox, methods=methods, provider=provider, uow=uow, clock=clock
    )


ReceivePaymentNoticeDep = Annotated[
    ReceivePaymentNotice, Depends(get_receive_payment_notice)
]
