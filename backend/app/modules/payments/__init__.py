"""The Payments context: a player's saved method, and the port money moves through.

Settled by ``docs/adr/0189`` §4–§5 and specified in the mechanics §12 and its
Appendix A. **The club is the seller**: every charge is made on the club's own
Stripe account and a player's card is saved once, on the platform, after terms
that name the club as the one charging.

Three things live here (#536, #541). The **Payment method** — an event-sourced
aggregate, one stream per player, filed under the player's own id — holds the
saved method and the consent it was saved under. The **payment provider** is
the one port every movement of money goes through, with two adapters: Stripe,
and an in-process fake that local runs, seeds and tests use. And the **Seat
charge** — one stream per payment for one player's share of one game — is the
fill's all or nothing: held, then taken with the booking or let go, the money
following the record from the outbox.
"""
