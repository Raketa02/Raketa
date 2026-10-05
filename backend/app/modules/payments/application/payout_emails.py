"""*A payout was sent*, as the club's desk reads it (#548; the mechanics §16.12;
the screens B9).

Sent once a payout is on its way — one a day at most, since a club is paid at
the close of each day its games are over. The words live here, beside the use
case that queues them (``docs/adr/0186`` §4); the wall clock is the club's,
Europe/Warsaw. **What the desk needs and nothing more**: how much, when it
should arrive, and how many games it is for — the games themselves are on the
Money page, which the button opens.
"""

from __future__ import annotations

from datetime import date
from typing import Final

from app.application.mail.layout import ButtonEmail, render
from app.application.ports.mail import OutgoingMessage
from app.kernel import Instant
from app.modules.clubs.domain.court_hours import local_day
from app.modules.payments.application.seat_charge_emails import zloty

#: The ``kind`` it is queued under — what outlives the purge.
PAYOUT_SENT_KIND: Final = "payments.payout_sent.club"


def _day(on: date) -> str:
    """*Saturday 10 October*."""

    return f"{on:%A} {on.day} {on:%B}"


def payout_sent_email(
    *,
    to: str,
    club: str,
    amount_grosze: int,
    games: int,
    day: date,
    arrives_at: Instant,
    link: str,
) -> OutgoingMessage:
    """*A payout was sent* — how much, for how many games, and when."""

    played = "1 game" if games == 1 else f"{games} games"
    return render(
        ButtonEmail(
            kind=PAYOUT_SENT_KIND,
            to=to,
            subject="A payout was sent",
            heading="A payout was sent",
            lines=(
                f"{zloty(amount_grosze)} is on its way to {club}'s bank account, "
                f"expected by {_day(local_day(arrives_at))}.",
                f"It is your money for {played} over by the close of {_day(day)}: "
                "what the players paid, less what was given back and the card "
                "fees.",
            ),
            button_label="Open Money",
            button_url=link,
        )
    )
