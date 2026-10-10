"""The Payment method aggregate — event-sourced, one stream per player.

A player's saved card or wallet, and the **consent** it was saved under
(``docs/adr/0189`` §5; the mechanics §12.5). Four rules shape it.

**The terms are accepted before anything is saved.** A setup opens without
them, and nothing can be saved out of it until they are recorded for it —
``save`` refuses a setup whose terms are missing, and the application layer
hands the phone the secret that confirms a setup only once they are.

**Change keeps the old method until the new one is saved.** A setup started
while a method is saved leaves it saved; only the save that ends the setup
replaces it, so a player who abandons a change is still charged the card they
had.

**The consent covers a brand.** It was given for a card of one network, and a
card whose bank moved it to another cannot be charged off-session until its
holder agrees again (the mechanics Appendix A). So ``terms_needed`` is read off
the stream — the brand the latest consent was given for, against the brand the
card has now — and never recorded. **And it covers the words**: consent given to
terms no longer in force asks again too (#637), since the fill holds only a
player who accepted the version in force.

**Born by being used**: ``unwritten`` is a player who never opened the setup,
and every act starts from it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable
from uuid import UUID

from app.kernel import Instant, instant, invariant
from app.modules.payments.domain.errors import (
    PaymentMethodNotFound,
    PaymentSetupNotStarted,
    PaymentSetupsExhausted,
    PaymentTermsNotAccepted,
    PaymentTermsOutdated,
)
from app.modules.payments.domain.events import (
    PaymentMethodChanged,
    PaymentMethodRemoved,
    PaymentMethodSaved,
    PaymentMethodUpdated,
    PaymentSetupStarted,
    PaymentTermsAccepted,
)
from app.modules.payments.domain.provider import CardOnFile, Wallet
from app.modules.payments.domain.terms import (
    PAYMENT_TERMS_VERSION,
    SETUPS_COUNTED_OVER,
    SETUPS_PER_DAY,
)
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder

_BRAND = re.compile(r"\A[a-z0-9_]{1,32}\Z")
_LAST_FOUR = re.compile(r"\A[0-9]{4}\Z")

#: The brand recorded for a network the provider names in a way nothing here
#: recognises — drawn as a plain card, and never a failed save.
UNKNOWN_BRAND = "unknown"


def card_brand(value: str) -> str:
    """The network as recorded: the provider's own word, lower case."""

    folded = value.strip().lower()
    return folded if _BRAND.match(folded) else UNKNOWN_BRAND


def last_four(value: str) -> str:
    """The card number's last four digits — all of it Raketa ever holds."""

    invariant(bool(_LAST_FOUR.match(value)), f"last four digits: {value!r}")
    return value


@dataclass(frozen=True, slots=True)
class SavedMethod:
    """The method a player is charged through, as the stream has it."""

    method_id: str
    brand: str
    last_four: str
    wallet: Wallet | None
    #: The setup that saved it.
    setup_id: str


@dataclass(frozen=True, slots=True)
class Consent:
    """The terms a player accepted: which, when, from where — and for which
    brand of card, since a new brand asks again."""

    terms_version: str
    accepted_at: Instant
    ip: str | None
    brand: str


@dataclass(frozen=True, slots=True)
class OpenSetup:
    """A setup started and not yet saved. ``terms`` is present once they were
    accepted for it — the only state its secret is handed out in."""

    setup_id: str
    terms: PaymentTermsAccepted | None = None


@dataclass
class PaymentMethod:
    """One player's saved method and consent, as the stream leaves them."""

    player_id: UUID
    #: The player's customer at the provider, from their first setup on.
    customer_id: str | None = None
    setup: OpenSetup | None = None
    method: SavedMethod | None = None
    consent: Consent | None = None
    #: When each setup was started, oldest first — the card-testing guard's
    #: count, read off the stream rather than kept anywhere else.
    setups_started_at: tuple[Instant, ...] = ()
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @classmethod
    def unwritten(cls, player_id: UUID) -> "PaymentMethod":
        """A player who never opened the payment setup."""

        return cls(player_id=player_id)

    @classmethod
    def from_history(
        cls, player_id: UUID, events: Iterable[DomainEvent]
    ) -> "PaymentMethod":
        payment_method = cls.unwritten(player_id)
        for event in events:
            payment_method._apply(event)
        return payment_method

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    # ------------------------------------------------------------------ reads

    @property
    def terms_needed(self) -> bool:
        """Whether the saved method waits on the terms being accepted again —
        its card is of another brand than the one they were accepted for, or
        they were accepted in words no longer in force (#637): the fill holds
        nothing on terms the player did not see."""

        return self.method is not None and (
            self.consent is None
            or self.consent.brand != self.method.brand
            or self.consent.terms_version != PAYMENT_TERMS_VERSION
        )

    @property
    def setups_counted(self) -> int:
        """How many setups this player ever started — what the next one's
        idempotency key counts from."""

        return len(self.setups_started_at)

    def refuse_when_setups_exhausted(self, *, at: Instant) -> None:
        """``payment_setups_exhausted`` once ``SETUPS_PER_DAY`` were started in
        the day before ``at``. Asked **before** the provider is, so a refused
        setup costs the provider nothing."""

        since = at - SETUPS_COUNTED_OVER
        if sum(1 for started in self.setups_started_at if started > since) >= (
            SETUPS_PER_DAY
        ):
            raise PaymentSetupsExhausted()

    # ------------------------------------------------------------------- acts

    def start_setup(self, *, setup_id: str, customer_id: str, at: Instant) -> None:
        """A setup opened at the provider. It **replaces** one left open, which
        saves nothing from now on and is named on the event, so that it can be
        cancelled at the provider after the commit; a method already saved
        stays saved."""

        invariant(
            self.customer_id in (None, customer_id),
            "a player's setups are all under one customer",
        )
        self.refuse_when_setups_exhausted(at=at)
        self._record_that(
            PaymentSetupStarted(
                player_id=self.player_id,
                setup_id=setup_id,
                customer_id=customer_id,
                replaced_setup_id=(
                    self.setup.setup_id if self.setup is not None else None
                ),
                occurred_at=at,
            )
        )

    def accept_terms(
        self, *, terms_version: str, ip: str | None, at: Instant
    ) -> str | None:
        """The player accepted the terms in force. Answers the setup they were
        accepted for — whose secret may now be handed out — or ``None`` when
        they were accepted again for the method already saved.

        **One press answers everything waiting on it**: the open setup's terms,
        and the saved card's too when its bank moved it to another brand — a
        *Change* started and abandoned leaves a setup open, and an acceptance
        that answered only that would leave the card waiting on terms the
        player has just accepted. Accepting again what nothing asks for records
        nothing, so a retried press is harmless; with nothing open and nothing
        saved there is nothing to accept terms for.
        """

        if terms_version != PAYMENT_TERMS_VERSION:
            raise PaymentTermsOutdated(in_force=PAYMENT_TERMS_VERSION)
        if self.setup is None and self.method is None:
            raise PaymentSetupNotStarted()
        if self.terms_needed:
            self._record_that(self._accepted(terms_version, ip, at, None))
        if self.setup is None:
            return None
        if self.setup.terms is None:
            self._record_that(self._accepted(terms_version, ip, at, self.setup))
        return self.setup.setup_id

    def save(self, *, setup_id: str, card: CardOnFile, at: Instant) -> SavedMethod:
        """The open setup saved ``card``. Refused before the terms; the same
        setup saved twice — the phone's confirmation and the provider's notice
        both arriving — records it once."""

        if self.method is not None and self.method.setup_id == setup_id:
            return self.method
        if self.setup is None or self.setup.setup_id != setup_id:
            raise PaymentSetupNotStarted()
        if self.setup.terms is None:
            raise PaymentTermsNotAccepted()
        brand, digits = card_brand(card.brand), last_four(card.last_four)
        wallet = card.wallet.value if card.wallet is not None else None
        if self.method is None:
            event: DomainEvent = PaymentMethodSaved(
                player_id=self.player_id,
                setup_id=setup_id,
                method_id=card.method_id,
                brand=brand,
                last_four=digits,
                wallet=wallet,
                occurred_at=at,
            )
        else:
            event = PaymentMethodChanged(
                player_id=self.player_id,
                setup_id=setup_id,
                method_id=card.method_id,
                brand=brand,
                last_four=digits,
                wallet=wallet,
                previous_method_id=self.method.method_id,
                occurred_at=at,
            )
        self._record_that(event)
        assert self.method is not None
        return self.method

    def remove(self, *, at: Instant) -> SavedMethod:
        """The player removed their method. Whether anything still needs it is
        the application's question, asked before this."""

        if self.method is None:
            raise PaymentMethodNotFound()
        removed = self.method
        self._record_that(
            PaymentMethodRemoved(
                player_id=self.player_id, method_id=removed.method_id, occurred_at=at
            )
        )
        return removed

    def bank_updated(self, card: CardOnFile, *, at: Instant) -> None:
        """The bank updated the saved card, as the provider reports it. A card
        that is not the saved one — released, or replaced since — and a report
        that changes nothing record nothing."""

        if self.method is None or self.method.method_id != card.method_id:
            return
        brand, digits = card_brand(card.brand), last_four(card.last_four)
        if (brand, digits) == (self.method.brand, self.method.last_four):
            return
        self._record_that(
            PaymentMethodUpdated(
                player_id=self.player_id,
                method_id=card.method_id,
                brand=brand,
                last_four=digits,
                occurred_at=at,
            )
        )

    # ------------------------------------------------------------------- fold

    def _accepted(
        self, terms_version: str, ip: str | None, at: Instant, setup: OpenSetup | None
    ) -> PaymentTermsAccepted:
        return PaymentTermsAccepted(
            player_id=self.player_id,
            terms_version=terms_version,
            ip=ip,
            setup_id=setup.setup_id if setup is not None else None,
            occurred_at=at,
        )

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, PaymentSetupStarted):
            self.customer_id = event.customer_id
            self.setup = OpenSetup(setup_id=event.setup_id)
            self.setups_started_at = (
                *self.setups_started_at,
                instant(event.occurred_at),
            )
        elif isinstance(event, PaymentTermsAccepted):
            if event.setup_id is None:
                assert self.method is not None
                self.consent = self._consent(event, brand=self.method.brand)
            elif self.setup is not None and self.setup.setup_id == event.setup_id:
                self.setup = OpenSetup(setup_id=self.setup.setup_id, terms=event)
        elif isinstance(event, (PaymentMethodSaved, PaymentMethodChanged)):
            accepted = self.setup.terms if self.setup is not None else None
            self.method = SavedMethod(
                method_id=event.method_id,
                brand=event.brand,
                last_four=event.last_four,
                wallet=Wallet(event.wallet) if event.wallet is not None else None,
                setup_id=event.setup_id,
            )
            self.consent = (
                self._consent(accepted, brand=event.brand)
                if accepted is not None
                else None
            )
            self.setup = None
        elif isinstance(event, PaymentMethodRemoved):
            self.method = None
            self.consent = None
        elif isinstance(event, PaymentMethodUpdated):
            assert self.method is not None
            self.method = SavedMethod(
                method_id=self.method.method_id,
                brand=event.brand,
                last_four=event.last_four,
                wallet=self.method.wallet,
                setup_id=self.method.setup_id,
            )
        else:
            raise TypeError(f"Unsupported payment method event {event!r}")
        self.version += 1

    @staticmethod
    def _consent(accepted: PaymentTermsAccepted, *, brand: str) -> Consent:
        return Consent(
            terms_version=accepted.terms_version,
            accepted_at=instant(accepted.occurred_at),
            ip=accepted.ip,
            brand=brand,
        )
