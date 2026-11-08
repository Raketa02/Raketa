"""**Ranking visibility** — the profile's fact behind *Show me in General*
(``docs/adr/0203`` §7; root ``CONTEXT.md``, *Player profile*).

Whether strangers find the player in the ranking: **on by default** — every
profile, one committed before the switch existed included, is ``SHOWN`` until
its player turns it — and changed by the player at any time, as a new event on
the profile's stream. The Rankings context follows it through the outbox: a
``HIDDEN`` player's row leaves everybody else's General, keeps its place, and
stays in their friends' Friends.

Two values rather than a boolean, because the route is
``/players/me/ranking-visibility`` and a body of ``{"visibility": "HIDDEN"}``
says what it does where ``{"shown": false}`` asks the reader to invert it.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class RankingVisibility(StrEnum):
    #: *Show me in General* on: listed for everybody.
    SHOWN = "SHOWN"
    #: Off: left out of everybody's General but the player's own.
    HIDDEN = "HIDDEN"


#: What every profile starts with, and what a stream that never turned the
#: switch folds to.
DEFAULT_RANKING_VISIBILITY: Final = RankingVisibility.SHOWN
