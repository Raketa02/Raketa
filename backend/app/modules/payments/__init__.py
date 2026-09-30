"""The Payments context: a player's saved method, and the port money moves through.

Settled by ``docs/adr/0189`` §4–§5 and specified in the mechanics §12 and its
Appendix A. **The club is the seller**: every charge is made on the club's own
Stripe account and a player's card is saved once, on the platform, after terms
that name the club as the one charging.

Two things live here today (#536). The **Payment method** — an event-sourced
aggregate, one stream per player, filed under the player's own id — holds the
saved method and the consent it was saved under. And the **payment provider**,
the one port every movement of money goes through, with two adapters: Stripe,
and an in-process fake that local runs, seeds and tests use. The **Seat charge**
arrives with the fill (#541).
"""
