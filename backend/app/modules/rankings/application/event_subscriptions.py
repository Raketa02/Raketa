"""Who the Rankings context hears. **It records no event of its own**, so it
registers nothing in the catalog.

**Two listeners**: the move, on the rating's ``rating.moved_on_result``, and
the switch, on the profile's ``player_profile.ranking_visibility_set`` (#772).
Both **write**, so each is subscribed per delivery run over that run's session
(``app/bootstrap/events.py``), as the level answerer is.
"""

from __future__ import annotations

from app.application.events import EventDispatcher
from app.modules.player_profile.domain.events import RankingVisibilitySet
from app.modules.rankings.application.projection import (
    FollowTheSwitch,
    MoveTheRanking,
)
from app.modules.rating.domain.events import RatingMovedOnResult


def subscribe_the_ranking_mover(
    dispatcher: EventDispatcher, mover: MoveTheRanking
) -> None:
    """A settled result moves its player's row the moment it is delivered —
    the same event that moved the Level (``docs/adr/0203`` §10)."""

    dispatcher.subscribe(RatingMovedOnResult, mover)


def subscribe_the_switch_follower(
    dispatcher: EventDispatcher, follower: FollowTheSwitch
) -> None:
    """*Show me in General* turned reaches the rows the moment it is
    delivered (``docs/adr/0203`` §7)."""

    dispatcher.subscribe(RankingVisibilitySet, follower)
