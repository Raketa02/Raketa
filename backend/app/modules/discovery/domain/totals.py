"""**A people row's total**: how many people it could show — **everybody who
qualifies, never its good matches** — so FOR YOU can draw *Players at your
level · 14* and *See all 14 ›* (``docs/adr/0205`` §6; #812). ADR-0205 calls
them the row's *pools*; the code doesn't, since **Pool** is the glossary's word
for whom a game is dealt to.

**What it counts** is the row's own qualifying condition under the row's own
exclusions — the reader, a block either way, *Show me to new people* off, an
account that doesn't play — **each person once**, however many sports or tags
put them there. *Same competitive level*: a level in a sport the reader holds
one in; *New in Raketa*: joined in the last 30 days; *Same vibe*: a Social tag
in common.

**It is counted up to 100 and no further** (``COUNTED_UP_TO``): the phone draws
*99+* past 99, so a count that went on would buy nothing on screen and cost a
scan of everybody who qualifies. 100 reads *100 or more*.

**Never a score**: a total counts who qualifies, so nothing is forecast,
compared or ranked to count it — not the 70% line, not two shared tags.
"""

from __future__ import annotations

from typing import Final

from app.kernel import invariant

#: Where a total stops: the phone draws *99+* past 99.
COUNTED_UP_TO: Final = 100


def capped(counted: int) -> int:
    """A count as a total says it: at most ``COUNTED_UP_TO``."""

    invariant(counted >= 0, f"a count of people: {counted}")
    return min(counted, COUNTED_UP_TO)
