"""Who the Rankings context hears. **It records no event of its own**, so it
registers nothing in the catalog.

**One listener**: the move, on the rating's ``rating.moved_on_result``. It
**writes**, so it is subscribed per delivery run over that run's session
(``app/bootstrap/events.py``), as the level answerer is.
"""

from __future__ import annotations

from app.application.events import EventDispatcher
from app.modules.rankings.application.projection import MoveTheRanking
from app.modules.rating.domain.events import RatingMovedOnResult


def subscribe_the_ranking_mover(
    dispatcher: EventDispatcher, mover: MoveTheRanking
) -> None:
    """A settled result moves its player's row the moment it is delivered —
    the same event that moved the Level (``docs/adr/0203`` §10)."""

    dispatcher.subscribe(RatingMovedOnResult, mover)
