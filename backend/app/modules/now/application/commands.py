"""What a caller asks Now for, and the one enumeration that asks it.

The request carries **the selected sport and nothing else**. In particular it
carries no stamp of what the phone is holding, and the server never answers
*nothing has changed*: Now is asked for rarely and only at moments where the
player is explicitly asking — arrival, a pull, an action, a countdown reaching
zero — and pull-to-refresh carries a promise (*what you are reading is real and I
am checking*) that a saved payload would break.

Switching sport is a **new request**, not a filter over a payload holding every
sport. The alternative pays for a rare act at the expense of the overwhelmingly
common one, opening the app, and would run the whole funnel once per declared
sport for a screen mostly looked at once.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from app.kernel import Sport


class SportFilter(str, Enum):
    """The sport bar's five fixed chips, as the one value the request carries.

    Four sports and ``all``. The four keep the sport registry's own spelling
    rather than gaining a second, lower-cased one — one name for one sport, and
    the client sends back the value it already holds. ``all`` is lower-case
    because it is not a sport, which is the distinction the case is carrying.
    """

    ALL = "all"
    PADEL = "PADEL"
    TENNIS = "TENNIS"
    SQUASH = "SQUASH"
    BADMINTON = "BADMINTON"

    @property
    def sport(self) -> Sport | None:
        """The one sport this filter names, or nothing when it names them all."""

        return None if self is SportFilter.ALL else Sport(self.value)


@dataclass(frozen=True)
class ComposeNowQuery:
    """Who is looking, and at which sport."""

    player_id: UUID
    sport: SportFilter = SportFilter.ALL
