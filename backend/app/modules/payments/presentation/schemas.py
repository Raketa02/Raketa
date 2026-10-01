"""The player surface's shapes for You › Payments (#536; the screens A7.3).

**No card number, no provider id and no consent record crosses.** A saved method
is drawn as its brand, its last four digits and the wallet it came through; the
setup's id crosses because the phone's provider fields confirm that setup, and
its **secret crosses once — as the answer to accepting the terms**, which is the
order the mechanics §12.5 requires. The address the terms were accepted from,
and when, are evidence on the player's stream and on no response.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.kernel import Sport
from app.modules.payments.application.seat_charges import Receipt, SeatChargeReading
from app.modules.payments.application.setup import SetupOpened
from app.modules.payments.domain.payment_method import PaymentMethod
from app.modules.payments.domain.provider import Wallet
from app.modules.payments.domain.seat_charge import FailureReason, SeatChargeStatus
from app.modules.payments.domain.terms import PAYMENT_TERMS_VERSION


class PaymentSetupResponse(BaseModel):
    """A setup opened: what the phone opens the provider's card fields with."""

    setup_id: str = Field(
        description=(
            "The setup the phone's provider fields confirm. **Its secret is not "
            "here**: it is the answer to accepting the terms, and nothing can be "
            "saved without it."
        )
    )
    publishable_key: str = Field(
        description=(
            "The key the provider's fields are opened with. Not a secret: it "
            "collects details and can charge nothing."
        )
    )
    terms_version: str = Field(
        description=(
            "The version of the payment terms in force — the words the client "
            "must show before *Accept and continue*, and send back."
        )
    )

    @classmethod
    def from_opened(cls, opened: SetupOpened) -> "PaymentSetupResponse":
        return cls(
            setup_id=opened.setup_id,
            publishable_key=opened.publishable_key,
            terms_version=opened.terms_version,
        )


class PaymentTermsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    terms_version: str = Field(
        description=(
            "The version of the words the player was shown. Anything but the "
            "terms in force is `409 payment_terms_outdated`."
        ),
    )


class PaymentTermsResponse(BaseModel):
    client_secret: str | None = Field(
        description=(
            "The secret the phone confirms the open setup with — its **only** "
            "appearance on any response. `null` when the terms were accepted "
            "again for the method already saved, after its bank moved it to "
            "another brand: there is nothing to confirm."
        )
    )


class SavedMethodSchema(BaseModel):
    brand: str = Field(
        description=(
            "The card network as the provider names it, lower case — `visa`, "
            "`mastercard`, `unknown` for one it does not recognise. An open set: "
            "draw a plain card for a brand you have no badge for."
        )
    )
    last_four: str = Field(description="The last four digits of the card number.")
    wallet: Wallet | None = Field(
        description=(
            "The phone's wallet it was saved through, or `null` for a card typed in."
        )
    )


class PaymentMethodResponse(BaseModel):
    """The player's payment method, as You › Payments draws it."""

    method: SavedMethodSchema | None = Field(
        description="The saved method, or `null` — *Not set up*."
    )
    terms_needed: bool = Field(
        description=(
            "`true` when the bank moved the saved card to another brand: it "
            "cannot be charged until the player accepts the terms again "
            "(`POST …/terms` with no setup open). Always `false` with no method."
        )
    )
    terms_version: str = Field(description="The version of the terms in force.")

    @classmethod
    def from_aggregate(cls, payment_method: PaymentMethod) -> "PaymentMethodResponse":
        saved = payment_method.method
        return cls(
            method=(
                SavedMethodSchema(
                    brand=saved.brand,
                    last_four=saved.last_four,
                    wallet=saved.wallet,
                )
                if saved is not None
                else None
            ),
            terms_needed=payment_method.terms_needed,
            terms_version=PAYMENT_TERMS_VERSION,
        )


# --------------------------------------------------------------------------- #
# Seat charges and receipts (#541)
# --------------------------------------------------------------------------- #


class SellerSchema(BaseModel):
    """The club a share is paid to — the seller, named on every receipt."""

    id: UUID
    name: str | None = Field(
        description="The club's name; `null` for a club that no longer exists."
    )


class PaymentToConfirmSchema(BaseModel):
    """What the phone confirms a refused payment with, on the club's account:
    the provider's own confirmation, with ``client_secret`` and the seller's
    account — **asked of the provider now and never recorded**."""

    client_secret: str = Field(
        description="The payment's secret. Confirm it in the provider's own fields."
    )
    connected_account_id: str = Field(
        description=(
            "The club's account at the provider — a direct charge is confirmed "
            "on the seller's account."
        )
    )
    publishable_key: str


class SeatChargeResponse(BaseModel):
    """One of the reader's own seat charges."""

    seat_charge_id: UUID
    proposal_id: UUID = Field(
        description="The game it was for — a booking takes the same id."
    )
    status: SeatChargeStatus = Field(
        description=(
            "`AUTHORISED` held, `FAILED` refused and waiting for its player, "
            "`TAKING`/`CAPTURED` paid, `RELEASING`/`CANCELLED` let go untaken."
        )
    )
    refusal: FailureReason | None = Field(
        description=(
            "Why it was refused: `AUTHENTICATION_REQUIRED` — confirm it in the "
            "app; `DECLINED` — confirm it with another card; `TERMS_NEEDED` — "
            "accept the terms again, then say yes; `NO_METHOD` — save a method, "
            "then say yes. `null` unless it was refused."
        )
    )
    amount_grosze: int
    sport: Sport
    starts_at: datetime
    club: SellerSchema
    to_confirm: PaymentToConfirmSchema | None = Field(
        description=(
            "Present exactly while the payment waits for its player: confirm it "
            "with this, then `POST /seat-charges/{id}/confirmation`."
        )
    )

    @classmethod
    def from_reading(cls, reading: SeatChargeReading) -> "SeatChargeResponse":
        charge = reading.charge
        confirm = reading.to_confirm
        return cls(
            seat_charge_id=charge.charge_id,
            proposal_id=charge.game_id,
            status=charge.status,
            refusal=charge.failure,
            amount_grosze=charge.amount_grosze,
            sport=charge.sport,
            starts_at=charge.starts_at,
            club=SellerSchema(id=charge.club_id, name=reading.club_name),
            to_confirm=(
                None
                if confirm is None
                else PaymentToConfirmSchema(
                    client_secret=confirm.client_secret,
                    connected_account_id=confirm.account_id,
                    publishable_key=confirm.publishable_key,
                )
            ),
        )


class ReceiptSchema(BaseModel):
    """One share the reader paid, or got back — *the club named as the
    seller*."""

    seat_charge_id: UUID = Field(
        description=(
            "The payment. A share refunded has two rows under one id — the "
            "charge and the refund — told apart by `kind`."
        )
    )
    kind: Literal["CHARGE", "REFUND"] = Field(
        description=(
            "`CHARGE` — a share paid (✓). `REFUND` — a share given back (↩): "
            "less the card fee to a player who left before the cut-off, whole "
            "on a game called off at its cut-off."
        )
    )
    club: SellerSchema
    sport: Sport
    starts_at: datetime
    amount_grosze: int = Field(
        description="What was paid, or what came back, in grosze — always positive."
    )
    card_fee_grosze: int | None = Field(
        description=(
            "On a `REFUND`, the card fee the provider kept back — nought on a "
            "refund in full. `null` on a `CHARGE`."
        )
    )
    paid_at: datetime = Field(
        description="When the money moved: taken, or — on a `REFUND` — given back."
    )


class ReceiptsResponse(BaseModel):
    """You › Payments' *RECEIPTS*, the latest first."""

    receipts: list[ReceiptSchema]

    @classmethod
    def from_receipts(cls, receipts: Sequence[Receipt]) -> "ReceiptsResponse":
        return cls(
            receipts=[
                ReceiptSchema(
                    seat_charge_id=receipt.charge.charge_id,
                    kind=receipt.kind.value,
                    club=SellerSchema(
                        id=receipt.charge.club_id, name=receipt.club_name
                    ),
                    sport=receipt.charge.sport,
                    starts_at=receipt.charge.starts_at,
                    amount_grosze=receipt.amount_grosze,
                    card_fee_grosze=receipt.card_fee_grosze,
                    paid_at=receipt.at,
                )
                for receipt in receipts
            ]
        )
