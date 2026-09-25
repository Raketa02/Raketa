"""*Forgot password?*'s own rules, beside the credential it issues.

Both are about the person asking and neither is configuration: how often one
address may be sent a reset is what stops the form being used to fill a
stranger's inbox, and the page a reset link opens is a path the web apps and
the app's link handling claim (``docs/adr/0186`` §3) — only the address in
front of it is a setting.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Final

#: Resets one address may be sent in one window (``docs/adr/0184`` §5). A
#: request past it gets the **identical answer** and sends nothing: a refusal
#: that only an address with an account could earn would be the enumeration the
#: identical answer exists to prevent.
RESET_REQUESTS_PER_WINDOW: Final = 3
RESET_REQUEST_WINDOW: Final = timedelta(hours=1)

#: The page a reset link opens, under the public site for a player or an
#: administrator and under the club website for a club: ``<site>/reset/<token>``.
RESET_PATH: Final = "/reset/"


@dataclass(frozen=True)
class ResetPage:
    """The page a reset link opens: a site's address, as configuration gives
    it, and ``/reset/`` under it. The address is normalised here — a trailing
    slash in a setting is the same site — so a link is never printed with two."""

    site: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "site", self.site.rstrip("/"))

    def link_to(self, token: str) -> str:
        return f"{self.site}{RESET_PATH}{token}"
