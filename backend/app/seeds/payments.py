"""The payment methods: every seeded player has a card saved — but one (#536).

**A seeded method is a setup somebody finished** (``docs/adr/0029``): each goes
through ``StartPaymentSetup``, ``AcceptPaymentTerms`` and
``ConfirmPaymentSetup`` in the order a phone takes them, so each player's
Payment method stream holds the setup, the terms accepted before anything was
saved, and the save — exactly what a request writes. Nothing here opens a
table.

**Through the fake provider, and the seed supplies what the phone typed**, as it
supplies the clock and a photograph's verdict: a card is typed into the
provider's own fields on a phone and never reaches the backend, so the fake is
told which of its cards was entered. The ids on the streams are the fake's
(``pm_fake_…``), which a laptop's API — on the fake as well — answers as the
card every seed saves.

**The arrangement is for the screens a developer signs in to.** The default
protagonist's card is the mock's *Card •••• 4312*; ``rated-in-every-sport``
saved a Mastercard through Google Pay and ``the-newcomer`` a Visa through Apple
Pay, so both wallet badges have somebody to be drawn for; everybody else in the
catalog and the cohort has ``A_CARD``, Visa •••• 4242, because every one of them
will be asked to say yes to a game and a yes needs a method. **``brand-new-player``
has none**, which is *Not set up* and the setup's first step.

**Re-running saves nobody's twice**: a player with a method saved is left as
they are — a developer who changed or removed theirs in the app keeps what
they did, except that a removed one is saved again, because the layer's promise
is that it is there.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Sequence, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_fake_payments,
    build_payment_method_repository,
    build_unit_of_work,
    build_user_repository,
)
from app.kernel import Instant
from app.modules.payments.application.commands import AcceptPaymentTermsCommand
from app.modules.payments.application.setup import (
    AcceptPaymentTerms,
    ConfirmPaymentSetup,
    StartPaymentSetup,
)
from app.modules.payments.domain.ports import PaymentMethodRepository
from app.modules.payments.domain.provider import Wallet
from app.modules.payments.domain.terms import PAYMENT_TERMS_VERSION
from app.modules.payments.domain.entered_cards import A_CARD, EnteredCard
from app.seeds.catalog import (
    ACCOUNTS,
    BRAND_NEW_PLAYER,
    RATED_IN_EVERY_SPORT,
    THE_NEWCOMER,
    THE_POPULATED_PLAYER,
)
from app.seeds.clock import FixedClock

#: Whose card is not ``A_CARD``, and what it is.
SEEDED_CARDS: Final[dict[str, EnteredCard]] = {
    THE_POPULATED_PLAYER.slug: EnteredCard(brand="visa", last_four="4312"),
    RATED_IN_EVERY_SPORT.slug: EnteredCard(
        brand="mastercard", last_four="5454", wallet=Wallet.GOOGLE_PAY
    ),
    THE_NEWCOMER.slug: EnteredCard(
        brand="visa", last_four="1881", wallet=Wallet.APPLE_PAY
    ),
}

#: Who is left with nothing saved — the setup's first step.
WITHOUT_A_METHOD: Final = (BRAND_NEW_PLAYER,)


@final
@dataclass(frozen=True, slots=True)
class SeededPaymentMethod:
    #: A catalog slug, or the cohort member's handle.
    who: str
    player_id: UUID
    card: EnteredCard | None
    #: Whether this run saved it, or found it saved.
    saved: bool


@final
@dataclass(frozen=True, slots=True)
class SeededPaymentMethods:
    methods: tuple[SeededPaymentMethod, ...]


async def write_the_payment_methods(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    now: Instant,
    cohort: Sequence[tuple[str, UUID]],
) -> SeededPaymentMethods:
    """Save a card for every named account but the ones left without, and for
    every cohort member — ``cohort`` is each member's handle and player id.

    **After the accounts and the cohort**, which it reads and never writes.
    Nothing below reads a method yet, so its position among the later layers is
    free; it runs early so a game the later tickets seed can be paid for.
    """

    # The fake, from the composition root as every adapter here is: the one
    # thing the seed supplies is what each player's phone typed into it.
    provider = build_fake_payments()

    async def saved(session: AsyncSession, player_id: UUID, card: EnteredCard) -> bool:
        """One player through the setup, unless a method is saved already."""

        if (await _methods(session).load(player_id)).method is not None:
            return False
        clock = FixedClock(at=now)
        uow = build_unit_of_work(session)
        opened = await StartPaymentSetup(
            methods=_methods(session), provider=provider, uow=uow, clock=clock
        ).execute(player_id)
        provider.phone_enters(opened.setup_id, card)
        await AcceptPaymentTerms(
            methods=_methods(session), provider=provider, uow=uow, clock=clock
        ).execute(
            # No address: a seed run accepted them, and saying otherwise would
            # be a piece of evidence nobody gave.
            AcceptPaymentTermsCommand(
                player_id=player_id, terms_version=PAYMENT_TERMS_VERSION, ip=None
            )
        )
        await ConfirmPaymentSetup(
            methods=_methods(session), provider=provider, uow=uow, clock=clock
        ).execute(player_id)
        return True

    methods: list[SeededPaymentMethod] = []
    async with session_factory() as session:
        users = build_user_repository(session)
        named: list[tuple[str, UUID, EnteredCard | None]] = []
        for account in ACCOUNTS:
            user = await users.get_by_email(account.email)
            if user is None:
                raise RuntimeError(
                    f"{account.slug} is not registered — the accounts layer runs first"
                )
            card = (
                None
                if account in WITHOUT_A_METHOD
                else SEEDED_CARDS.get(account.slug, A_CARD)
            )
            named.append((account.slug, user.id, card))
    for who, player_id, card in (
        *named,
        *((handle, player_id, A_CARD) for handle, player_id in cohort),
    ):
        was_saved = False
        if card is not None:
            async with session_factory() as session:
                was_saved = await saved(session, player_id, card)
        methods.append(
            SeededPaymentMethod(
                who=who, player_id=player_id, card=card, saved=was_saved
            )
        )
    return SeededPaymentMethods(methods=tuple(methods))


def _methods(session: AsyncSession) -> PaymentMethodRepository:
    return build_payment_method_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def payment_method_lines(seeded: SeededPaymentMethods) -> list[str]:
    """The report's section: who has what, and who has nothing on purpose."""

    saved = sum(1 for method in seeded.methods if method.saved)
    lines = [
        "Payment methods (fake provider)",
        f"  {saved} saved by this run, "
        f"{sum(1 for m in seeded.methods if m.card is not None)} players with one",
    ]
    for method in seeded.methods:
        if method.who in SEEDED_CARDS or method.card is None:
            lines.append(f"  {method.who}: {_described(method.card)}")
    return lines


def _described(card: EnteredCard | None) -> str:
    if card is None:
        return "nothing saved — Not set up"
    wallet = f" through {card.wallet.value}" if card.wallet is not None else ""
    return f"{card.brand} •••• {card.last_four}{wallet}"
