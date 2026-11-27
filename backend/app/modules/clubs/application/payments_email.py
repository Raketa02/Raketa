"""*Stripe needs something from you*, as the desk reads it (the mechanics
§16.12, the screens B9).

Sent at once, and only for an account that **was taking payments and
stopped** (``domain/payments_account.py``): the club is off players' decks
until it answers, and nobody at the desk may be looking at its Overview. The
button is the club website's *continue* page, which asks for a fresh link to
the provider's pages and follows it.
"""

from __future__ import annotations

from typing import Final

from app.application.mail.layout import ButtonEmail, render
from app.application.ports.mail import OutgoingMessage

#: The ``kind`` it is queued under — what outlives the purge.
PAYMENTS_NEED_ATTENTION_KIND: Final = "payments.needs_attention.club"


def payments_need_attention_email(*, to: str, club: str, link: str) -> OutgoingMessage:
    return render(
        ButtonEmail(
            kind=PAYMENTS_NEED_ATTENTION_KIND,
            to=to,
            subject="Stripe needs something from you",
            heading="Stripe needs something from you",
            lines=(
                f"Stripe needs more details about {club} before it can take "
                f"payments for you and pay them out again.",
                "Until then, your courts aren't offered to Rakieta players. "
                "Games already booked go ahead as booked.",
            ),
            button_label="Continue with Stripe",
            button_url=link,
        )
    )
