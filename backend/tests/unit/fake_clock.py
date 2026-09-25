"""A clock a test moves by hand.

The **controllable clock** the API fixtures run the whole application on
(``docs/adr/0186`` §5): a one-hour expiry is checked by moving it an hour rather
than by waiting one. Structural rather than a subclass of ``Clock``, as every
stand-in in this suite is.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.kernel import Instant, instant


class MovableClock:
    def __init__(self, at: datetime) -> None:
        self.at = at

    def now(self) -> Instant:
        return instant(self.at)

    def move(self, by: timedelta) -> None:
        self.at = self.at + by
