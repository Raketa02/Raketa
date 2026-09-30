"""The player surface's shapes for You › Payments (#536; the screens A7.3).

**No card number, no provider id and no consent record crosses.** A saved method
is drawn as its brand, its last four digits and the wallet it came through; the
setup's id crosses because the phone's provider fields confirm that setup, and
its **secret crosses once — as the answer to accepting the terms**, which is the
order the mechanics §12.5 requires. The address the terms were accepted from,
and when, are evidence on the player's stream and on no response.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.modules.payments.application.setup import SetupOpened
from app.modules.payments.domain.payment_method import PaymentMethod
from app.modules.payments.domain.provider import Wallet
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
