"""Which surface a token may be presented on (``docs/adr/0185`` §6).

Two identities sign in to this backend and they must never be confused: a
**User**, on the player app, and a **Club account**, on the club website
(``docs/adr/0182`` §3). A club token presented to the player surface is refused,
and a player's to the club surface, even when both were issued for one email —
which is allowed, because the two are unrelated accounts with two passwords.

**Each audience has exactly one kind of account behind it**, which is why a
refresh token that records its audience records whose it is: the player app's
sessions belong to Users — an Administrator included, because that profile runs
inside the player app and switching to it is client state rather than a new
token — and the club website's belong to Club accounts.

**A token with no audience is a player-app token.** Every token issued before
this record carried none, and they were all issued to players; reading them as
anything else would sign every existing session out on deploy. The window closes
by time alone, once the last of them has expired, and a later record that stops
accepting them has to check that it has.
"""

from __future__ import annotations

from enum import Enum


class Audience(str, Enum):
    """The surface a token was issued for, carried as its ``aud`` claim."""

    PLAYER_APP = "player_app"
    CLUB = "club"


#: What a token that names no audience is read as (see the module docstring).
UNSTATED_AUDIENCE = Audience.PLAYER_APP
