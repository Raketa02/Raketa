"""What the card fee on a share comes to — **an estimate**, said before the
money moves (#544; the mechanics §12.3, §13, §18).

The provider never returns its processing fee on a refund, so a player leaving
before the club's cut-off is refunded their share **less the card fee** — and
the *Leave the game* sheet says how much before they confirm (*"You'll be
refunded 38,40 zł now (the 1,60 zł card fee isn't returned)"*). What the
provider actually kept is on the refund it answers (``Refund.fee_withheld_grosze``)
and on the receipt; this is the figure the sheet quotes: Stripe's standard
price for a card issued in the EEA, which is what nearly every Polish card is.
"""

from __future__ import annotations

#: Stripe's standard EEA card price in Poland: 1.5 % and 1,00 zł (the
#: mechanics Appendix A, §18) — about 1,60 zł on a 40 zł share.
_FEE_PER_MILLE = 15
_FEE_FIXED_GROSZE = 100


def estimated_card_fee(amount_grosze: int) -> int:
    """The card fee on a payment of ``amount_grosze``, half a grosz rounding
    up."""

    return (amount_grosze * _FEE_PER_MILLE + 500) // 1000 + _FEE_FIXED_GROSZE
