"""The Club context: a place players search, and the account its desk signs in with.

Settled by ``docs/adr/0182``. A **Club** is event-sourced, with a synchronous
search projection written in the same transaction; its **Club account** is a
second aggregate, never folded into the club, because a club's facts are public
— searched by every player — and its credentials are not. The account signs in
only on the club surface (``app/api/v1/club.py``), under the club audience
(``docs/adr/0185`` §6).
"""
