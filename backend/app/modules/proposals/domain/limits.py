"""The numbers a proposal is held to (the mechanics §6.6, §7, §18).

**Domain, never configuration**: each is a promise the product makes to a player
— how many people one game may be dealt to, how many games they may be In on at
once — and an environment that could select one would be an environment that
decides how the deck behaves.
"""

from __future__ import annotations

from typing import Final

#: How many views of one game may be dealt, each to different people.
VERSIONS_PER_PROPOSAL: Final = 3

#: How many next best fits one open seat is dealt to at once, after a no.
NEXT_BEST_FITS_PER_SEAT: Final = 3

#: How many yeses a player may have on games that have not filled, **per sport**.
#: A post counts as one: posting is the poster's yes.
LIVE_YESES_PER_SPORT: Final = 10

#: How far from a player group's home club the other clubs whose courts it may
#: use lie, in kilometres (the mechanics §4.3, §18). An official group's is its
#: club's own setting.
PLAYER_GROUP_CLUBS_WITHIN_KM: Final = 10
