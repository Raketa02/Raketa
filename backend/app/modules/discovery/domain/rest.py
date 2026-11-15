"""**Resting** — a card the reader keeps scrolling past steps aside
(``docs/adr/0204`` §7, §10; the home-rows mechanics §9.2, Q34).

Pure: the days are counted by the rest count, the relation handed in.

- **On screen** is the phone's word: a card at least half visible (call 2 of
  #790), reported for a row and a batch of player ids. **One count per card,
  row and Warsaw day** — the same day reported twice counts once — and a day
  the phone never reports counts nothing, so opening Home without scrolling to
  the row rests nobody.
- **A day counts only while the pair is unconnected**: nothing between them, or
  they asked the reader. A friend or somebody the reader asked is a gap
  whatever is counted, and a day they were connected never rests them later.
- **Five different days rest the player in that row**, and **each row keeps its
  own count**: Kuba resting in *Same vibe* is fresh in *Same competitive
  level*. **The count never resets** (call 9 of #790).
- **A rested player is a gap, never hidden**: §9.1's rule (``fresh_then_gaps``)
  takes them with the friends, the requests sent and the weaker matches, so they
  come back on a row with room, and See all lists them where they fall.
- **Only the two rows that rest are reported**: *New in Raketa* turns over by
  itself, and no See all rests anybody (§9.3).
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Final

from app.kernel import Instant
from app.modules.discovery.domain.new_in_raketa import DAYS_IN
from app.modules.discovery.domain.relation import Relation

#: Different days on screen that rest a player in a row.
RESTS_AFTER: Final = 5
#: The most cards one report may name — a row holds ten, re-read through a
#: day; more is a client's bug.
A_REPORT: Final = 50


class OnScreenRow(StrEnum):
    """A row whose cards rest — each with its own count."""

    SAME_LEVEL = "SAME_LEVEL"
    SAME_VIBE = "SAME_VIBE"


def day_on_screen(now: Instant) -> date:
    """The Warsaw day a report made ``now`` counts for."""

    return now.astimezone(DAYS_IN).date()


def counts_toward_rest(relation: Relation) -> bool:
    """Whether a day on screen counts — only while the pair is unconnected."""

    return not relation.connected


def has_rested(days: int) -> bool:
    """Five different days on screen or more."""

    return days >= RESTS_AFTER
