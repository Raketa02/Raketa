"""The payment terms: which words are in force, and how many setups a day.

**The words are the client's; the version is here.** The text a player reads
is shipped with the screen that shows it, and what the backend records is the
**identifier** of it, never the prose — freezing copy in history is how a
wording change becomes a migration. What the backend owns is *which* version is
in force, because the fill will charge only a player who accepted it.

The text is the mechanics §12.5, and it is **reviewed by a lawyer before
launch** (open item O3); the reviewed words ship under a new version, and the
setup's answer carries the version in force so a client can tell it is showing
old words.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Final

#: The payment terms in force, named by the day their words were settled: the
#: mechanics §12.5, as grilled on 2026-09-29.
PAYMENT_TERMS_VERSION: Final = "2026-09-29"

#: At most this many setups started in any day, per player (the mechanics
#: Appendix A, *card testing*): card testers target card-saving, and a signed-in
#: account that opens a sixth setup in a day is not somebody changing their
#: mind about a card. Counted from the stream, so it needs no clock of its own.
SETUPS_PER_DAY: Final = 5
SETUPS_COUNTED_OVER: Final = timedelta(days=1)
